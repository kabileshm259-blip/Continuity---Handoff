from typing import Dict, List, Optional, Any
import threading
from datetime import datetime
from app.repositories.base import BaseRepository
from app.models.enums import (
    CaseStatus, Priority, WorkItemStatus, CommitmentStatus,
    BlockerStatus, ExceptionStatus
)
from app.models.case import (
    Case, TaskItem, Commitment, Blocker, ExceptionItem,
    AuditEvent, Handoff
)

class InMemoryRepository(BaseRepository):
    """Thread-safe in-memory repository for CONTINUITY.
    
    Used for local development, hackathon demos, and automated testing
    without requiring AWS DynamoDB credentials.
    """

    def __init__(self, seed: bool = True):
        self._lock = threading.Lock()
        self._cases: Dict[str, Case] = {}
        self._handoffs: Dict[str, Handoff] = {}
        if seed:
            self._seed_data()

    def _seed_data(self):
        """Seed realistic workplace cases."""
        now_str = datetime.now().strftime("%I:%M %p")
        
        # CASE-1042: Customer replacement request
        case_1042 = Case(
            case_id="CASE-1042",
            title="Customer replacement request",
            description="Replacement order for customer damaged goods received during transit. Requires warehouse stock verification.",
            owner="Arun Kumar",
            status=CaseStatus.UNRESOLVED,
            priority=Priority.MEDIUM,
            deadline="Tomorrow",
            customer="Priya",
            created_at="Today, 09:30 AM",
            updated_at=f"Today, {now_str}",
            original_context="I handled the replacement request from Priya. Customer sent the damaged product photos yesterday. I already contacted warehouse and they said they should confirm stock by tomorrow. I promised the customer that I would update her by Friday.",
            next_action="Follow up with warehouse tomorrow morning",
            evidence="Damaged item photographs attached in ticket #4491. S3 bucket archive: s3://continuity-evidence/damaged-1042.jpg",
            tasks=[
                TaskItem(
                    task_id="TASK-1042-1",
                    case_id="CASE-1042",
                    title="Review customer damage photos",
                    status=WorkItemStatus.COMPLETED,
                    owner="Arun Kumar",
                    next_action="Archived in ticket"
                ),
                TaskItem(
                    task_id="TASK-1042-2",
                    case_id="CASE-1042",
                    title="Warehouse replacement stock verification",
                    status=WorkItemStatus.IN_PROGRESS,
                    owner="Priya Sharma",
                    next_action="Call warehouse manager at 9 AM"
                )
            ],
            commitments=[
                Commitment(
                    commitment_id="COM-1042-1",
                    case_id="CASE-1042",
                    description="Update customer by Friday with dispatch tracking",
                    committed_to="Priya (Customer)",
                    expected_date="Friday",
                    status=CommitmentStatus.ACTIVE
                )
            ],
            blockers=[
                Blocker(
                    blocker_id="BLK-1042-1",
                    case_id="CASE-1042",
                    description="Waiting for warehouse confirmation on replacement inventory",
                    blocked_by="Warehouse Team",
                    status=BlockerStatus.ACTIVE
                )
            ],
            exceptions=[],
            audit_history=[
                AuditEvent(
                    event_id="EVT-1042-1",
                    case_id="CASE-1042",
                    timestamp="10:12 AM",
                    actor="Arun Kumar",
                    action="Handoff initiated",
                    details="Prepared handoff summary for replacement intake."
                ),
                AuditEvent(
                    event_id="EVT-1042-2",
                    case_id="CASE-1042",
                    timestamp="10:13 AM",
                    actor="AI Extraction Layer",
                    action="Extracted commitment",
                    details="Promised customer update by Friday; identified warehouse blocker."
                ),
                AuditEvent(
                    event_id="EVT-1042-3",
                    case_id="CASE-1042",
                    timestamp="10:13 AM",
                    actor="Policy Engine",
                    action="Status evaluated",
                    details="Classified as UNRESOLVED: Action items pending with warehouse dependency."
                ),
                AuditEvent(
                    event_id="EVT-1042-4",
                    case_id="CASE-1042",
                    timestamp="10:14 AM",
                    actor="System",
                    action="Assigned to Priya Sharma",
                    details="Work item transitioned into Priya Sharma's Continuity Queue."
                ),
                AuditEvent(
                    event_id="EVT-1042-5",
                    case_id="CASE-1042",
                    timestamp="10:20 AM",
                    actor="Priya Sharma",
                    action="Warehouse inquiry logged",
                    details="Priya requested warehouse confirmation for stock reservation."
                )
            ]
        )

        # CASE-1038: Invoice correction
        case_1038 = Case(
            case_id="CASE-1038",
            title="Invoice correction",
            description="Billing adjustment for corporate account Apex Logistics due to volume discount discrepancy.",
            owner="Arun Kumar",
            status=CaseStatus.AT_RISK,
            priority=Priority.HIGH,
            deadline="Today",
            customer="Apex Logistics",
            created_at="Today, 08:45 AM",
            updated_at=f"Today, {now_str}",
            original_context="For the invoice correction, finance hasn't approved the change yet. I sent them the updated invoice this morning. If they don't respond today, someone should follow up.",
            next_action="Follow up with Finance",
            evidence="Discrepancy audit sheet #INV-992. Updated credit note draft sent to finance-ops@apex.internal.",
            tasks=[
                TaskItem(
                    task_id="TASK-1038-1",
                    case_id="CASE-1038",
                    title="Send updated invoice to Finance",
                    status=WorkItemStatus.COMPLETED,
                    owner="Arun Kumar"
                ),
                TaskItem(
                    task_id="TASK-1038-2",
                    case_id="CASE-1038",
                    title="Obtain Finance Director sign-off",
                    status=WorkItemStatus.BLOCKED,
                    owner="Priya Sharma",
                    next_action="Ping Finance team via Teams channel"
                )
            ],
            commitments=[],
            blockers=[
                Blocker(
                    blocker_id="BLK-1038-1",
                    case_id="CASE-1038",
                    description="Finance approval pending on $14,200 credit adjustment",
                    blocked_by="Finance Department",
                    status=BlockerStatus.ACTIVE
                )
            ],
            exceptions=[],
            audit_history=[
                AuditEvent(
                    event_id="EVT-1038-1",
                    case_id="CASE-1038",
                    timestamp="09:15 AM",
                    actor="Arun Kumar",
                    action="Invoice submitted",
                    details="Sent corrected invoice revision to Finance ops queue."
                ),
                AuditEvent(
                    event_id="EVT-1038-2",
                    case_id="CASE-1038",
                    timestamp="10:13 AM",
                    actor="Policy Engine",
                    action="Status classified as AT RISK",
                    details="Deadline is Today while Finance approval is unresolved."
                )
            ]
        )

        # CASE-8821: Wrong item / SKU conflict
        case_8821 = Case(
            case_id="CASE-8821",
            title="Wrong item / SKU conflict",
            description="Discrepancy on order #8821. Customer received industrial pump model B instead of model A, while WMS logs indicate model A was scanned.",
            owner="Arun Kumar",
            status=CaseStatus.EXCEPTION,
            priority=Priority.HIGH,
            deadline="Today, 5:00 PM",
            customer="Zenith Manufacturing",
            created_at="Today, 10:00 AM",
            updated_at=f"Today, {now_str}",
            original_context="Also there is one issue with order #8821. Customer says they received the wrong item but the warehouse system shows the correct SKU. I haven't figured out which one is correct yet.",
            next_action="Verify shipment evidence",
            evidence="Warehouse barcode dispatch log: SKU-A4492 (Scan timestamp 07:14 AM). Customer unboxing photo shows SKU-B1109.",
            tasks=[
                TaskItem(
                    task_id="TASK-8821-1",
                    case_id="CASE-8821",
                    title="Retrieve packing bay surveillance & barcode logs",
                    status=WorkItemStatus.IN_PROGRESS,
                    owner="Priya Sharma",
                    next_action="Cross-reference packing station 4 video"
                )
            ],
            commitments=[],
            blockers=[],
            exceptions=[
                ExceptionItem(
                    exception_id="EXC-8821-1",
                    case_id="CASE-8821",
                    expected="Warehouse record and customer delivery should match",
                    found="Customer reports different item received (SKU-B1109)",
                    evidence="Warehouse system shows correct SKU (SKU-A4492), but customer unboxing photo confirms wrong model.",
                    impact="Inventory miscount and customer manufacturing delay",
                    required_action="Verify shipment evidence and dispatch emergency replacement if confirmed",
                    status=ExceptionStatus.ACTIVE
                )
            ],
            audit_history=[
                AuditEvent(
                    event_id="EVT-8821-1",
                    case_id="CASE-8821",
                    timestamp="08:45 AM",
                    actor="Customer Intake",
                    action="Discrepancy reported",
                    details="Customer ticket opened with attached photos of incorrect item."
                ),
                AuditEvent(
                    event_id="EVT-8821-2",
                    case_id="CASE-8821",
                    timestamp="10:13 AM",
                    actor="Policy Engine",
                    action="Status classified as EXCEPTION",
                    details="Expected warehouse manifest conflicts with physical delivery report."
                )
            ]
        )

        # CASE-1050: Support follow-up
        case_1050 = Case(
            case_id="CASE-1050",
            title="Enterprise tier-2 support follow-up",
            description="Follow-up on intermittent API latency reported by CloudScale partners during high concurrency.",
            owner="Arun Kumar",
            status=CaseStatus.UNRESOLVED,
            priority=Priority.MEDIUM,
            deadline="In 3 days",
            customer="CloudScale Partners",
            created_at="Yesterday, 04:00 PM",
            updated_at=f"Today, {now_str}",
            original_context="CloudScale reported 400ms latency spikes. Preliminary metrics gathered. Needs joint review call.",
            next_action="Schedule technical architecture review with CloudScale IT",
            evidence="Datadog dashboard link and trace ID sample log #DD-9921",
            tasks=[],
            commitments=[
                Commitment(
                    commitment_id="COM-1050-1",
                    case_id="CASE-1050",
                    description="Provide root-cause analysis report",
                    committed_to="CloudScale CTO",
                    expected_date="Thursday 3 PM",
                    status=CommitmentStatus.ACTIVE
                )
            ],
            blockers=[],
            exceptions=[],
            audit_history=[
                AuditEvent(
                    event_id="EVT-1050-1",
                    case_id="CASE-1050",
                    timestamp="Yesterday, 04:15 PM",
                    actor="Arun Kumar",
                    action="Case logged",
                    details="Captured initial CloudScale diagnostic traces."
                )
            ]
        )

        # CASE-1055: Pending approval
        case_1055 = Case(
            case_id="CASE-1055",
            title="Vendor SLA contract renewal",
            description="Annual renewal agreement for logistics partner QuickFreight. Rates renegotiated; waiting on legal sign-off.",
            owner="Arun Kumar",
            status=CaseStatus.BLOCKED,
            priority=Priority.HIGH,
            deadline="Next Monday",
            customer="QuickFreight Corp",
            created_at="2 days ago",
            updated_at=f"Today, {now_str}",
            original_context="Contract agreed with vendor. Sent to legal 3 days ago for compliance approval.",
            next_action="Awaiting Legal redline feedback",
            evidence="Contract draft v2.4 in DocuSign queue #DS-88201",
            tasks=[],
            commitments=[],
            blockers=[
                Blocker(
                    blocker_id="BLK-1055-1",
                    case_id="CASE-1055",
                    description="Legal compliance audit pending on indemnification clause",
                    blocked_by="Legal Department",
                    status=BlockerStatus.ACTIVE
                )
            ],
            exceptions=[],
            audit_history=[
                AuditEvent(
                    event_id="EVT-1055-1",
                    case_id="CASE-1055",
                    timestamp="2 days ago",
                    actor="Arun Kumar",
                    action="Submitted to Legal",
                    details="Contract document placed in Legal review queue."
                ),
                AuditEvent(
                    event_id="EVT-1055-2",
                    case_id="CASE-1055",
                    timestamp="Today, 09:00 AM",
                    actor="Policy Engine",
                    action="Status classified as BLOCKED",
                    details="External Legal dependency blocks execution."
                )
            ]
        )

        self._cases = {
            "CASE-1042": case_1042,
            "CASE-1038": case_1038,
            "CASE-8821": case_8821,
            "CASE-1050": case_1050,
            "CASE-1055": case_1055
        }

    def get_all_cases(self) -> List[Case]:
        with self._lock:
            return list(self._cases.values())

    def get_case(self, case_id: str) -> Optional[Case]:
        with self._lock:
            return self._cases.get(case_id)

    def save_case(self, case: Case) -> Case:
        with self._lock:
            case.updated_at = datetime.now().strftime("%I:%M %p")
            self._cases[case.case_id] = case
            return case

    def save_handoff(self, handoff: Handoff) -> Handoff:
        with self._lock:
            self._handoffs[handoff.handoff_id] = handoff
            return handoff

    def get_handoff(self, handoff_id: str) -> Optional[Handoff]:
        with self._lock:
            return self._handoffs.get(handoff_id)

    def add_audit_event(self, case_id: str, actor: str, action: str, details: str) -> Optional[AuditEvent]:
        with self._lock:
            case = self._cases.get(case_id)
            if not case:
                return None
            event_id = f"EVT-{case_id}-{len(case.audit_history) + 1}"
            timestamp = datetime.now().strftime("%I:%M %p")
            event = AuditEvent(
                event_id=event_id,
                case_id=case_id,
                timestamp=timestamp,
                actor=actor,
                action=action,
                details=details
            )
            case.audit_history.append(event)
            case.updated_at = timestamp
            return event

    def health_check(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "provider": "memory",
                "status": "healthy",
                "total_cases": len(self._cases)
            }
