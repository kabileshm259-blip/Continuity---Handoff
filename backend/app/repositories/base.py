from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.case import Case, Handoff, AuditEvent

class BaseRepository(ABC):
    """Abstract base repository defining the persistence contract for CONTINUITY."""

    @abstractmethod
    def get_all_cases(self) -> List[Case]:
        """Retrieve all active cases."""
        pass

    @abstractmethod
    def get_case(self, case_id: str) -> Optional[Case]:
        """Retrieve a specific case by its unique identifier."""
        pass

    @abstractmethod
    def save_case(self, case: Case) -> Case:
        """Create or update a case."""
        pass

    @abstractmethod
    def save_handoff(self, handoff: Handoff) -> Handoff:
        """Record raw handoff context."""
        pass

    @abstractmethod
    def get_handoff(self, handoff_id: str) -> Optional[Handoff]:
        """Retrieve a recorded handoff by its unique identifier."""
        pass

    @abstractmethod
    def add_audit_event(self, case_id: str, actor: str, action: str, details: str) -> Optional[AuditEvent]:
        """Append an immutable audit event to a case's history."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform a lightweight repository connectivity check."""
        pass
