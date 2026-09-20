from typing import Optional, Tuple
from datetime import datetime, timezone, timedelta
from app.models.enums import CaseStatus, Priority

class PolicyEngine:
    """Deterministic policy engine for workplace handoff operations.
    
    CRITICAL ARCHITECTURAL PRINCIPLE:
    AI extracts and explains.
    Code decides and enforces.
    
    The AI extracts facts (commitments, blockers, deadlines, exceptions).
    This engine evaluates those facts against strict operational rules.
    """

    DEFAULT_APPROACHING_THRESHOLD_HOURS = 24

    @classmethod
    def parse_deadline_proximity(
        cls,
        deadline_str: Optional[str],
        as_of: Optional[datetime] = None,
        approaching_threshold_hours: int = DEFAULT_APPROACHING_THRESHOLD_HOURS
    ) -> Tuple[bool, bool]:
        """Evaluates whether a deadline is past or approaching using UTC timestamps or textual terms.
        
        Returns:
            (is_past_deadline, is_approaching_deadline)
        """
        if not deadline_str:
            return False, False

        now_utc = as_of if as_of is not None else datetime.now(timezone.utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.replace(tzinfo=timezone.utc)

        # 1. Attempt ISO / timestamp parsing
        parsed_dt: Optional[datetime] = None
        cleaned = deadline_str.strip()
        
        # Replace trailing 'Z' with '+00:00' for standard fromisoformat parsing
        iso_str = cleaned
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1] + "+00:00"

        # Try standard ISO parsing
        try:
            parsed_dt = datetime.fromisoformat(iso_str)
        except (ValueError, TypeError):
            # Try common date/time formats
            for fmt in (
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%d-%m-%Y",
                "%m/%d/%Y",
                "%Y/%m/%d"
            ):
                try:
                    parsed_dt = datetime.strptime(cleaned, fmt)
                    break
                except (ValueError, TypeError):
                    continue

        if parsed_dt is not None:
            if parsed_dt.tzinfo is None:
                # Naive datetime: treat as UTC
                parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
            else:
                parsed_dt = parsed_dt.astimezone(timezone.utc)

            threshold = timedelta(hours=approaching_threshold_hours)
            if parsed_dt < now_utc:
                return True, False
            elif now_utc <= parsed_dt <= (now_utc + threshold):
                return False, True
            else:
                return False, False

        # 2. Fallback to relative textual keywords
        dl_lower = cleaned.lower()
        if any(term in dl_lower for term in ["yesterday", "passed", "overdue", "expired"]):
            return True, False
        elif any(term in dl_lower for term in ["today", "tomorrow", "tonight", "urgent", "eod", "immediate"]):
            return False, True

        return False, False

    @classmethod
    def evaluate_status(
        cls,
        is_completed: bool,
        has_exception: bool,
        has_active_blocker: bool,
        deadline_str: Optional[str] = None,
        is_unfinished: bool = True,
        as_of: Optional[datetime] = None,
        approaching_threshold_hours: int = DEFAULT_APPROACHING_THRESHOLD_HOURS
    ) -> Tuple[CaseStatus, Priority, str]:
        """Evaluates operational status, priority, and rationale based on deterministic business rules."""
        
        # Rule 1: Completed work
        if is_completed and not has_exception and not has_active_blocker and not is_unfinished:
            return (
                CaseStatus.RESOLVED,
                Priority.LOW,
                "Case resolved: All deliverables confirmed completed with no outstanding blockers."
            )

        # Rule 2: Expected information conflicts with actual information
        if has_exception:
            return (
                CaseStatus.EXCEPTION,
                Priority.HIGH,
                "Policy Engine classified as EXCEPTION: System records conflict with actual delivery or reported state."
            )

        # Evaluate deadline proximity (UTC timestamp or textual heuristics)
        is_past_deadline, is_approaching_deadline = cls.parse_deadline_proximity(
            deadline_str=deadline_str,
            as_of=as_of,
            approaching_threshold_hours=approaching_threshold_hours
        )

        # Rule 3: Deadline has passed
        if is_past_deadline:
            return (
                CaseStatus.OVERDUE,
                Priority.URGENT,
                f"Policy Engine classified as OVERDUE: Target deadline '{deadline_str}' has elapsed."
            )

        # Rule 4: Deadline is approaching AND blocker exists
        if is_approaching_deadline and has_active_blocker:
            return (
                CaseStatus.AT_RISK,
                Priority.HIGH,
                f"Policy Engine classified as AT RISK: Approaching deadline ('{deadline_str}') is constrained by an active blocker."
            )

        # Rule 5: Blocker exists
        if has_active_blocker:
            return (
                CaseStatus.BLOCKED,
                Priority.HIGH,
                "Policy Engine classified as BLOCKED: Work cannot progress due to an unresolved external dependency."
            )

        # Rule 6: Unfinished work default
        return (
            CaseStatus.UNRESOLVED,
            Priority.MEDIUM,
            "Policy Engine classified as UNRESOLVED: Action items remain pending with no immediate critical blockers."
        )
