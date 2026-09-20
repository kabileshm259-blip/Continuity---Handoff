import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.models.case import Case, AuditEvent
from app.models.enums import (
    CaseStatus, Priority, CommitmentStatus, BlockerStatus, ExceptionStatus
)
from app.policy.engine import PolicyEngine
from app.repositories.base import BaseRepository
from app.repositories.factory import get_repository

class CaseEvaluationDetail(BaseModel):
    case_id: str
    previous_status: str
    new_status: str
    previous_priority: str
    new_priority: str
    changed: bool
    reason: str
    deadline: Optional[str] = None

class DeadlineEvaluationSummary(BaseModel):
    evaluated: int = 0
    changed: int = 0
    at_risk: int = 0
    overdue: int = 0
    unchanged: int = 0
    details: List[CaseEvaluationDetail] = Field(default_factory=list)

class DeadlineEvaluationService:
    """Deterministic service for evaluating case deadlines and applying automated status transitions.
    
    Architectural principle:
    AI extracts facts (commitments, deadlines, blockers).
    Deterministic code decides and enforces.
    
    Guarantees:
    - Pure deterministic evaluation against UTC time.
    - Idempotent: re-running against unchanged conditions produces 0 transitions and 0 duplicate audit events.
    """

    def __init__(self, repo: Optional[BaseRepository] = None, approaching_threshold_hours: int = 24):
        self.repo = repo or get_repository()
        self.approaching_threshold_hours = approaching_threshold_hours

    def evaluate_case(
        self,
        case: Case,
        as_of: Optional[datetime] = None
    ) -> Tuple[bool, CaseStatus, Priority, str, Optional[str]]:
        """Evaluates a single case against its deadline and commitments.
        
        Returns:
            (has_changed, new_status, new_priority, rationale, effective_deadline)
        """
        now_utc = as_of if as_of is not None else datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        # Rule: Do not re-evaluate already RESOLVED cases
        if case.status == CaseStatus.RESOLVED:
            return False, case.status, case.priority, "Case is already resolved.", case.deadline

        # Determine effective deadline: case.deadline or first active commitment date
        effective_deadline = case.deadline
        if not effective_deadline and case.commitments:
            for com in case.commitments:
                if com.status == CommitmentStatus.ACTIVE and com.expected_date:
                    effective_deadline = com.expected_date
                    break

        has_exception = any(e.status == ExceptionStatus.ACTIVE for e in case.exceptions)
        has_active_blocker = any(b.status == BlockerStatus.ACTIVE for b in case.blockers)

        new_status, new_priority, rationale = PolicyEngine.evaluate_status(
            is_completed=False,
            has_exception=has_exception,
            has_active_blocker=has_active_blocker,
            deadline_str=effective_deadline,
            is_unfinished=True,
            as_of=now_utc,
            approaching_threshold_hours=self.approaching_threshold_hours
        )

        # Idempotency check: only changed if status or priority differs
        has_changed = (new_status != case.status) or (new_priority != case.priority)
        return has_changed, new_status, new_priority, rationale, effective_deadline

    def evaluate_all_cases(
        self,
        as_of: Optional[datetime] = None
    ) -> DeadlineEvaluationSummary:
        """Evaluates all cases in the repository and applies state transitions idempotently."""
        now_utc = as_of if as_of is not None else datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        cases = self.repo.get_all_cases()
        summary = DeadlineEvaluationSummary()
        summary.evaluated = len(cases)

        for case in cases:
            has_changed, new_status, new_priority, rationale, effective_deadline = self.evaluate_case(
                case, as_of=now_utc
            )

            detail = CaseEvaluationDetail(
                case_id=case.case_id,
                previous_status=case.status.value if hasattr(case.status, 'value') else str(case.status),
                new_status=new_status.value if hasattr(new_status, 'value') else str(new_status),
                previous_priority=case.priority.value if hasattr(case.priority, 'value') else str(case.priority),
                new_priority=new_priority.value if hasattr(new_priority, 'value') else str(new_priority),
                changed=has_changed,
                reason=rationale,
                deadline=effective_deadline
            )
            summary.details.append(detail)

            if has_changed:
                prev_status_str = detail.previous_status
                new_status_str = detail.new_status
                case.status = new_status
                case.priority = new_priority
                case.updated_at = f"Automated update, {now_utc.strftime('%Y-%m-%d %H:%M UTC')}"

                # Append auditable event for the automated transition
                audit_event = AuditEvent(
                    event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                    case_id=case.case_id,
                    timestamp=now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    actor="SYSTEM",
                    action="CASE_STATUS_CHANGED",
                    details=(
                        f"Automated transition from {prev_status_str} to {new_status_str} "
                        f"(Priority: {new_priority.value}). Reason: {rationale}. "
                        f"Deadline: '{effective_deadline}'. Evaluated at: {now_utc.isoformat()}."
                    )
                )
                case.audit_history.append(audit_event)
                self.repo.save_case(case)
                summary.changed += 1
            else:
                summary.unchanged += 1

            # Count final statuses
            final_status = new_status if has_changed else case.status
            if final_status == CaseStatus.AT_RISK:
                summary.at_risk += 1
            elif final_status == CaseStatus.OVERDUE:
                summary.overdue += 1

        return summary
