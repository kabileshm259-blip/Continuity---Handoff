import uuid
from datetime import datetime
from typing import List, Dict, Any
from app.models.case import (
    Handoff, HandoffRequest, HandoffResponse, Case, TaskItem,
    Commitment, Blocker, ExceptionItem, AuditEvent
)
from app.models.enums import (
    CaseStatus, Priority, WorkItemStatus, CommitmentStatus,
    BlockerStatus, ExceptionStatus
)
from app.ai.factory import get_ai_provider
from app.policy.engine import PolicyEngine
from app.storage.repository import get_repository
from app.evidence.factory import get_evidence_service

class HandoffService:
    def __init__(self):
        self.repo = get_repository()
        self.ai_provider = get_ai_provider()
        self.evidence_service = get_evidence_service()

    async def process_handoff(self, request: HandoffRequest) -> HandoffResponse:
        handoff_id = f"HND-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()
        now_str = now.strftime("%I:%M %p")
        
        # 1. Record raw handoff
        handoff = Handoff(
            handoff_id=handoff_id,
            outgoing_employee=request.outgoing_employee,
            incoming_employee=request.incoming_employee,
            raw_notes=request.raw_notes,
            created_at=f"Today, {now_str}",
            processed_at=f"Today, {now_str}"
        )
        self.repo.save_handoff(handoff)

        # 2. AI Fact Extraction (facts only, no policy decision)
        facts = await self.ai_provider.extract_work_state(request.raw_notes)

        cases_updated = []
        cases_created = []

        # Map extracted items by case_hint
        grouped_commitments = {}
        for c in facts.commitments:
            key = c.case_hint or "DEFAULT"
            grouped_commitments.setdefault(key, []).append(c)

        grouped_blockers = {}
        for b in facts.blockers:
            key = b.case_hint or "DEFAULT"
            grouped_blockers.setdefault(key, []).append(b)

        grouped_exceptions = {}
        for e in facts.exceptions:
            key = e.case_hint or "DEFAULT"
            grouped_exceptions.setdefault(key, []).append(e)

        grouped_next_actions = {}
        for n in facts.next_actions:
            key = n.case_hint or "DEFAULT"
            grouped_next_actions.setdefault(key, []).append(n)

        # Check existing cases that need updates
        all_cases = self.repo.get_all_cases()
        all_case_ids = {c.case_id: c for c in all_cases}

        # Update matching existing cases
        for case_id, case in all_case_ids.items():
            has_relevant_info = (
                case_id in grouped_commitments or
                case_id in grouped_blockers or
                case_id in grouped_exceptions or
                case_id in grouped_next_actions or
                case_id.lower() in request.raw_notes.lower()
            )

            if has_relevant_info:
                # Update owner to incoming employee
                previous_owner = case.owner
                case.owner = request.incoming_employee

                # Store raw handoff notes as evidence in S3/evidence storage
                evidence_meta = self.evidence_service.upload_evidence(
                    case_id=case_id,
                    content=request.raw_notes,
                    content_type="text/plain",
                    filename=f"handoff-{handoff_id}.txt",
                    created_by=request.outgoing_employee,
                    description="Raw workplace handoff notes"
                )
                case.evidence_records.append(evidence_meta)

                # Log EVIDENCE_CREATED audit event (without sensitive raw content)
                self.repo.add_audit_event(
                    case_id=case_id,
                    actor=request.outgoing_employee,
                    action="EVIDENCE_CREATED",
                    details=f"Raw handoff notes archived ({evidence_meta.object_key}, {evidence_meta.size_bytes} bytes). Evidence ID: {evidence_meta.evidence_id}"
                )

                # Append newly extracted commitments
                for c in grouped_commitments.get(case_id, []):
                    case.commitments.append(
                        Commitment(
                            commitment_id=f"COM-{case_id}-{len(case.commitments)+1}",
                            case_id=case_id,
                            description=c.description,
                            committed_to=c.committed_to,
                            expected_date=c.expected_date,
                            status=CommitmentStatus.ACTIVE
                        )
                    )

                # Append newly extracted blockers
                for b in grouped_blockers.get(case_id, []):
                    case.blockers.append(
                        Blocker(
                            blocker_id=f"BLK-{case_id}-{len(case.blockers)+1}",
                            case_id=case_id,
                            description=b.description,
                            blocked_by=b.blocked_by,
                            status=BlockerStatus.ACTIVE
                        )
                    )

                # Append newly extracted exceptions
                for e in grouped_exceptions.get(case_id, []):
                    case.exceptions.append(
                        ExceptionItem(
                            exception_id=f"EXC-{case_id}-{len(case.exceptions)+1}",
                            case_id=case_id,
                            expected=e.expected,
                            found=e.found,
                            evidence=e.evidence,
                            impact=e.impact,
                            required_action=e.required_action,
                            status=ExceptionStatus.ACTIVE
                        )
                    )

                # Update next action
                if case_id in grouped_next_actions:
                    case.next_action = grouped_next_actions[case_id][0].action

                # 3. Deterministic Policy Evaluation
                has_active_blockers = any(b.status == BlockerStatus.ACTIVE for b in case.blockers)
                has_active_exceptions = any(e.status == ExceptionStatus.ACTIVE for e in case.exceptions)
                
                new_status, new_priority, rationale = PolicyEngine.evaluate_status(
                    is_completed=case.status == CaseStatus.RESOLVED,
                    has_exception=has_active_exceptions,
                    has_active_blocker=has_active_blockers,
                    deadline_str=case.deadline,
                    is_unfinished=True
                )

                case.status = new_status
                case.priority = new_priority

                # 4. Append Audit Trail
                self.repo.add_audit_event(
                    case_id=case_id,
                    actor=request.outgoing_employee,
                    action="Handoff submitted",
                    details=f"Work context handed off from {previous_owner} to {request.incoming_employee}."
                )
                self.repo.add_audit_event(
                    case_id=case_id,
                    actor="Policy Engine",
                    action=f"Operational status: {new_status.value}",
                    details=rationale
                )

                self.repo.save_case(case)
                cases_updated.append(case_id)

        # If there were standalone exceptions or unresolved items not mapped to existing cases, create a new case
        unmapped_exceptions = grouped_exceptions.get("DEFAULT", [])
        unmapped_unresolved = [u for u in facts.unresolved if not u.case_hint or u.case_hint not in all_case_ids]

        should_create_case = (
            bool(unmapped_exceptions) or
            bool(unmapped_unresolved) or
            (not cases_updated and (
                bool(grouped_commitments.get("DEFAULT")) or
                bool(grouped_blockers.get("DEFAULT")) or
                bool(grouped_next_actions.get("DEFAULT")) or
                bool(facts.deadlines)
            ))
        )

        if should_create_case:
            new_case_id = f"CASE-{uuid.uuid4().hex[:4].upper()}"
            if unmapped_unresolved:
                title = unmapped_unresolved[0].title
            elif unmapped_exceptions:
                title = f"Exception: {unmapped_exceptions[0].expected}"
            elif facts.commitments:
                title = f"Commitment: {facts.commitments[0].description}"
            elif facts.next_actions:
                title = f"Action: {facts.next_actions[0].action}"
            else:
                title = "Operational handoff item"
            
            has_exc = len(unmapped_exceptions) > 0
            has_blk = len(grouped_blockers.get("DEFAULT", [])) > 0
            
            # Use extracted deadline if present
            case_deadline = None
            if facts.deadlines:
                case_deadline = facts.deadlines[0].date_str
            elif facts.commitments and facts.commitments[0].expected_date:
                case_deadline = facts.commitments[0].expected_date
            else:
                case_deadline = "In 2 days"

            status, priority, rationale = PolicyEngine.evaluate_status(
                is_completed=False,
                has_exception=has_exc,
                has_active_blocker=has_blk,
                deadline_str=case_deadline,
                is_unfinished=True
            )

            # Store raw handoff notes as evidence in S3/evidence storage
            evidence_meta = self.evidence_service.upload_evidence(
                case_id=new_case_id,
                content=request.raw_notes,
                content_type="text/plain",
                filename=f"handoff-{handoff_id}.txt",
                created_by=request.outgoing_employee,
                description="Raw workplace handoff notes"
            )

            new_case = Case(
                case_id=new_case_id,
                title=title,
                description="Auto-generated from handoff notes.",
                owner=request.incoming_employee,
                status=status,
                priority=priority,
                deadline=case_deadline,
                created_at=f"Today, {now_str}",
                updated_at=f"Today, {now_str}",
                original_context=request.raw_notes[:300],
                next_action=facts.next_actions[0].action if facts.next_actions else "Review handoff details",
                evidence_records=[evidence_meta],
                commitments=[
                    Commitment(
                        commitment_id=f"COM-{new_case_id}-1",
                        case_id=new_case_id,
                        description=c.description,
                        committed_to=c.committed_to,
                        expected_date=c.expected_date
                    ) for c in grouped_commitments.get("DEFAULT", [])
                ],
                blockers=[
                    Blocker(
                        blocker_id=f"BLK-{new_case_id}-1",
                        case_id=new_case_id,
                        description=b.description,
                        blocked_by=b.blocked_by
                    ) for b in grouped_blockers.get("DEFAULT", [])
                ],
                exceptions=[
                    ExceptionItem(
                        exception_id=f"EXC-{new_case_id}-1",
                        case_id=new_case_id,
                        expected=e.expected,
                        found=e.found,
                        evidence=e.evidence,
                        required_action=e.required_action
                    ) for e in unmapped_exceptions
                ],
                audit_history=[
                    AuditEvent(
                        event_id=f"EVT-{new_case_id}-1",
                        case_id=new_case_id,
                        timestamp=now_str,
                        actor=request.outgoing_employee,
                        action="EVIDENCE_CREATED",
                        details=f"Raw handoff notes archived ({evidence_meta.object_key}, {evidence_meta.size_bytes} bytes). Evidence ID: {evidence_meta.evidence_id}"
                    ),
                    AuditEvent(
                        event_id=f"EVT-{new_case_id}-2",
                        case_id=new_case_id,
                        timestamp=now_str,
                        actor=request.outgoing_employee,
                        action="Case created via handoff",
                        details=f"New operational case generated from handoff notes for {request.incoming_employee}."
                    ),
                    AuditEvent(
                        event_id=f"EVT-{new_case_id}-3",
                        case_id=new_case_id,
                        timestamp=now_str,
                        actor="Policy Engine",
                        action=f"Operational status: {status.value}",
                        details=rationale
                    )
                ]
            )
            self.repo.save_case(new_case)
            cases_created.append(new_case_id)

        all_active_cases = self.repo.get_all_cases()

        return HandoffResponse(
            handoff_id=handoff_id,
            outgoing_employee=request.outgoing_employee,
            incoming_employee=request.incoming_employee,
            processed_at=f"Today, {now_str}",
            cases_updated=cases_updated,
            cases_created=cases_created,
            extraction_summary={
                "completed_count": len(facts.completed),
                "unresolved_count": len(facts.unresolved),
                "commitments_count": len(facts.commitments),
                "blockers_count": len(facts.blockers),
                "deadlines_count": len(facts.deadlines),
                "exceptions_count": len(facts.exceptions),
                "next_actions_count": len(facts.next_actions)
            },
            cases=all_active_cases
        )
