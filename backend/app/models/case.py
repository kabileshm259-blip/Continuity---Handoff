from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.enums import (
    CaseStatus, Priority, ActionType, WorkItemStatus,
    CommitmentStatus, BlockerStatus, ExceptionStatus
)

class TaskItem(BaseModel):
    task_id: str
    case_id: str
    title: str
    status: WorkItemStatus = WorkItemStatus.PENDING
    owner: Optional[str] = None
    next_action: Optional[str] = None

class Commitment(BaseModel):
    commitment_id: str
    case_id: str
    description: str
    committed_to: str
    expected_date: Optional[str] = None
    status: CommitmentStatus = CommitmentStatus.ACTIVE

class Blocker(BaseModel):
    blocker_id: str
    case_id: str
    description: str
    blocked_by: str
    status: BlockerStatus = BlockerStatus.ACTIVE

class ExceptionItem(BaseModel):
    exception_id: str
    case_id: str
    expected: str
    found: str
    evidence: str
    impact: Optional[str] = None
    required_action: str
    status: ExceptionStatus = ExceptionStatus.ACTIVE

class AuditEvent(BaseModel):
    event_id: str
    case_id: str
    timestamp: str
    actor: str
    action: str
    details: str

class EvidenceMetadata(BaseModel):
    evidence_id: str
    case_id: str
    object_key: str
    content_type: str = "text/plain"
    original_filename: Optional[str] = None
    created_at: str
    created_by: str = "system"
    size_bytes: int = 0
    description: Optional[str] = None

class Case(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = ""
    owner: str
    status: CaseStatus = CaseStatus.UNRESOLVED
    priority: Priority = Priority.MEDIUM
    deadline: Optional[str] = None
    customer: Optional[str] = None
    created_at: str
    updated_at: str
    original_context: Optional[str] = None
    next_action: Optional[str] = None
    evidence: Optional[str] = None
    evidence_records: List[EvidenceMetadata] = Field(default_factory=list)
    tasks: List[TaskItem] = Field(default_factory=list)
    commitments: List[Commitment] = Field(default_factory=list)
    blockers: List[Blocker] = Field(default_factory=list)
    exceptions: List[ExceptionItem] = Field(default_factory=list)
    audit_history: List[AuditEvent] = Field(default_factory=list)

class Handoff(BaseModel):
    handoff_id: str
    outgoing_employee: str
    incoming_employee: str
    raw_notes: str
    created_at: str
    processed_at: Optional[str] = None

class HandoffRequest(BaseModel):
    outgoing_employee: str = "Arun Kumar"
    incoming_employee: str = "Priya Sharma"
    raw_notes: str
    handoff_date: Optional[str] = "Today"

class HandoffResponse(BaseModel):
    handoff_id: str
    outgoing_employee: str
    incoming_employee: str
    processed_at: str
    cases_updated: List[str]
    cases_created: List[str]
    extraction_summary: Dict[str, Any]
    cases: List[Case]

class ActionRequest(BaseModel):
    action: ActionType
    actor: str
    new_owner: Optional[str] = None
    reason: Optional[str] = None

class QueueStats(BaseModel):
    unresolved: int = 0
    at_risk: int = 0
    blocked: int = 0
    exceptions: int = 0
    overdue: int = 0
    total: int = 0

class QueueResponse(BaseModel):
    stats: QueueStats
    cases: List[Case]
