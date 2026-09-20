from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException
from app.models.case import Case, ActionRequest, QueueResponse, QueueStats, AuditEvent
from app.models.enums import CaseStatus, Priority, ActionType
from app.storage.repository import get_repository

class CaseService:
    def __init__(self):
        self.repo = get_repository()

    def get_case(self, case_id: str) -> Case:
        case = self.repo.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")
        return case

    def get_all_cases(self) -> List[Case]:
        return self.repo.get_all_cases()

    def get_queue(self, owner_filter: Optional[str] = None) -> QueueResponse:
        cases = self.repo.get_all_cases()
        if owner_filter:
            cases = [c for c in cases if c.owner.lower() == owner_filter.lower()]

        unresolved = sum(1 for c in cases if c.status == CaseStatus.UNRESOLVED)
        at_risk = sum(1 for c in cases if c.status == CaseStatus.AT_RISK)
        blocked = sum(1 for c in cases if c.status == CaseStatus.BLOCKED)
        exceptions = sum(1 for c in cases if c.status == CaseStatus.EXCEPTION)
        overdue = sum(1 for c in cases if c.status == CaseStatus.OVERDUE)
        total = len(cases)

        return QueueResponse(
            stats=QueueStats(
                unresolved=unresolved,
                at_risk=at_risk,
                blocked=blocked,
                exceptions=exceptions,
                overdue=overdue,
                total=total
            ),
            cases=cases
        )

    def execute_action(self, case_id: str, request: ActionRequest) -> Case:
        case = self.get_case(case_id)
        now_str = datetime.now().strftime("%I:%M %p")

        if request.action == ActionType.RESOLVE:
            case.status = CaseStatus.RESOLVED
            details = request.reason or "Case marked as resolved by employee."
            self.repo.add_audit_event(
                case_id=case_id,
                actor=request.actor,
                action="Marked Resolved",
                details=details
            )

        elif request.action == ActionType.REASSIGN:
            if not request.new_owner:
                raise HTTPException(status_code=400, detail="New owner must be specified for reassignment.")
            prev_owner = case.owner
            case.owner = request.new_owner
            details = f"Reassigned from {prev_owner} to {request.new_owner}. Reason: {request.reason or 'Shift transition'}"
            self.repo.add_audit_event(
                case_id=case_id,
                actor=request.actor,
                action=f"Reassigned to {request.new_owner}",
                details=details
            )

        elif request.action == ActionType.ESCALATE:
            case.priority = Priority.URGENT
            if case.status != CaseStatus.EXCEPTION:
                case.status = CaseStatus.AT_RISK
            details = f"Case escalated to URGENT priority. Reason: {request.reason or 'Critical deadline risk'}"
            self.repo.add_audit_event(
                case_id=case_id,
                actor=request.actor,
                action="Escalated to Urgent",
                details=details
            )

        case.updated_at = f"Today, {now_str}"
        return self.repo.save_case(case)
