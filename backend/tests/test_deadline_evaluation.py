import os
import unittest
from datetime import datetime, timezone, timedelta

from app.models.case import Case, TaskItem, Commitment, Blocker, ExceptionItem, AuditEvent
from app.models.enums import (
    CaseStatus, Priority, WorkItemStatus, CommitmentStatus, BlockerStatus, ExceptionStatus
)
from app.policy.engine import PolicyEngine
from app.repositories.memory_repository import InMemoryRepository
from app.services.deadline_service import DeadlineEvaluationService

class TestDeadlineEvaluation(unittest.TestCase):

    def setUp(self):
        self.repo = InMemoryRepository(seed=False)
        self.service = DeadlineEvaluationService(repo=self.repo, approaching_threshold_hours=24)
        self.base_time = datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc)

    def _create_case(
        self,
        case_id: str = "CASE-T1",
        status: CaseStatus = CaseStatus.UNRESOLVED,
        priority: Priority = Priority.MEDIUM,
        deadline: str = None,
        has_blocker: bool = False,
        commitments: list = None
    ) -> Case:
        blockers = []
        if has_blocker:
            blockers.append(Blocker(
                blocker_id=f"BLK-{case_id}",
                case_id=case_id,
                description="Waiting on vendor response",
                blocked_by="Vendor",
                status=BlockerStatus.ACTIVE
            ))

        return Case(
            case_id=case_id,
            title=f"Test Case {case_id}",
            owner="Priya Sharma",
            status=status,
            priority=priority,
            deadline=deadline,
            created_at="2026-09-20T08:00:00Z",
            updated_at="2026-09-20T08:00:00Z",
            blockers=blockers,
            commitments=commitments or [],
            audit_history=[
                AuditEvent(
                    event_id="EVT-INIT",
                    case_id=case_id,
                    timestamp="2026-09-20T08:00:00Z",
                    actor="Arun Kumar",
                    action="Case Created",
                    details="Initial intake"
                )
            ]
        )

    def test_1_deadline_in_future_remains_unchanged(self):
        """1. Deadline in the future (> 24h) remains unchanged with UNRESOLVED status."""
        future_dt = (self.base_time + timedelta(days=5)).isoformat()
        case = self._create_case(case_id="CASE-FUT", deadline=future_dt)
        self.repo.save_case(case)

        summary = self.service.evaluate_all_cases(as_of=self.base_time)
        self.assertEqual(summary.evaluated, 1)
        self.assertEqual(summary.changed, 0)
        self.assertEqual(summary.unchanged, 1)

        updated = self.repo.get_case("CASE-FUT")
        self.assertEqual(updated.status, CaseStatus.UNRESOLVED)
        self.assertEqual(len(updated.audit_history), 1)

    def test_2_deadline_passed_transitions_to_overdue(self):
        """2. Deadline that has elapsed transitions to OVERDUE with URGENT priority."""
        past_dt = (self.base_time - timedelta(hours=2)).isoformat()
        case = self._create_case(case_id="CASE-PAST", deadline=past_dt)
        self.repo.save_case(case)

        summary = self.service.evaluate_all_cases(as_of=self.base_time)
        self.assertEqual(summary.evaluated, 1)
        self.assertEqual(summary.changed, 1)
        self.assertEqual(summary.overdue, 1)

        updated = self.repo.get_case("CASE-PAST")
        self.assertEqual(updated.status, CaseStatus.OVERDUE)
        self.assertEqual(updated.priority, Priority.URGENT)
        self.assertEqual(len(updated.audit_history), 2)
        self.assertEqual(updated.audit_history[-1].action, "CASE_STATUS_CHANGED")
        self.assertEqual(updated.audit_history[-1].actor, "SYSTEM")
        self.assertIn("OVERDUE", updated.audit_history[-1].details)

    def test_3_approaching_deadline_with_blocker_transitions_to_at_risk(self):
        """3. Deadline approaching within 24h with an active blocker transitions to AT_RISK."""
        approaching_dt = (self.base_time + timedelta(hours=8)).isoformat()
        case = self._create_case(case_id="CASE-RISK", deadline=approaching_dt, has_blocker=True)
        self.repo.save_case(case)

        summary = self.service.evaluate_all_cases(as_of=self.base_time)
        self.assertEqual(summary.evaluated, 1)
        self.assertEqual(summary.changed, 1)
        self.assertEqual(summary.at_risk, 1)

        updated = self.repo.get_case("CASE-RISK")
        self.assertEqual(updated.status, CaseStatus.AT_RISK)
        self.assertEqual(updated.priority, Priority.HIGH)
        self.assertEqual(len(updated.audit_history), 2)
        self.assertEqual(updated.audit_history[-1].action, "CASE_STATUS_CHANGED")

    def test_4_rerunning_evaluation_is_idempotent(self):
        """4. Re-running evaluation on already transitioned case produces 0 changes and no duplicate audits."""
        past_dt = (self.base_time - timedelta(hours=5)).isoformat()
        case = self._create_case(case_id="CASE-IDEMP", deadline=past_dt)
        self.repo.save_case(case)

        # First run: transitions to OVERDUE
        run1 = self.service.evaluate_all_cases(as_of=self.base_time)
        self.assertEqual(run1.changed, 1)
        self.assertEqual(run1.overdue, 1)

        case_after_run1 = self.repo.get_case("CASE-IDEMP")
        audit_count_after_run1 = len(case_after_run1.audit_history)
        self.assertEqual(audit_count_after_run1, 2)

        # Second run: must be completely idempotent
        run2 = self.service.evaluate_all_cases(as_of=self.base_time)
        self.assertEqual(run2.changed, 0)
        self.assertEqual(run2.unchanged, 1)
        self.assertEqual(run2.overdue, 1)

        case_after_run2 = self.repo.get_case("CASE-IDEMP")
        self.assertEqual(len(case_after_run2.audit_history), audit_count_after_run1)

    def test_5_already_overdue_produces_no_duplicate_audit(self):
        """5. A case created already as OVERDUE produces no transition and no new audit event."""
        case = self._create_case(
            case_id="CASE-PRE-OVERDUE",
            status=CaseStatus.OVERDUE,
            priority=Priority.URGENT,
            deadline="yesterday"
        )
        self.repo.save_case(case)

        summary = self.service.evaluate_all_cases(as_of=self.base_time)
        self.assertEqual(summary.changed, 0)
        self.assertEqual(summary.overdue, 1)

        updated = self.repo.get_case("CASE-PRE-OVERDUE")
        self.assertEqual(len(updated.audit_history), 1)

    def test_6_multiple_cases_summary_counts(self):
        """6. Multiple diverse cases evaluate with correct aggregate summary counts."""
        # 1: overdue
        self.repo.save_case(self._create_case(
            case_id="C-1",
            deadline=(self.base_time - timedelta(hours=1)).isoformat()
        ))
        # 2: at risk (approaching + blocker)
        self.repo.save_case(self._create_case(
            case_id="C-2",
            deadline=(self.base_time + timedelta(hours=4)).isoformat(),
            has_blocker=True
        ))
        # 3: unchanged (future)
        self.repo.save_case(self._create_case(
            case_id="C-3",
            deadline=(self.base_time + timedelta(days=3)).isoformat()
        ))
        # 4: resolved (should be skipped)
        self.repo.save_case(self._create_case(
            case_id="C-4",
            status=CaseStatus.RESOLVED,
            deadline=(self.base_time - timedelta(days=2)).isoformat()
        ))

        summary = self.service.evaluate_all_cases(as_of=self.base_time)
        self.assertEqual(summary.evaluated, 4)
        self.assertEqual(summary.changed, 2)  # C-1 and C-2 changed
        self.assertEqual(summary.overdue, 1)
        self.assertEqual(summary.at_risk, 1)
        self.assertEqual(summary.unchanged, 2)

    def test_7_textual_deadline_heuristics(self):
        """7. Textual deadline terms ('yesterday', 'tomorrow' + blocker) evaluate deterministically."""
        case_yesterday = self._create_case(case_id="C-TEXT-1", deadline="yesterday")
        case_tomorrow_blocker = self._create_case(case_id="C-TEXT-2", deadline="tomorrow", has_blocker=True)
        self.repo.save_case(case_yesterday)
        self.repo.save_case(case_tomorrow_blocker)

        summary = self.service.evaluate_all_cases()
        self.assertEqual(summary.overdue, 1)
        self.assertEqual(summary.at_risk, 1)
        self.assertEqual(summary.changed, 2)

        c1 = self.repo.get_case("C-TEXT-1")
        c2 = self.repo.get_case("C-TEXT-2")
        self.assertEqual(c1.status, CaseStatus.OVERDUE)
        self.assertEqual(c2.status, CaseStatus.AT_RISK)

if __name__ == "__main__":
    unittest.main()
