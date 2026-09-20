from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict, Any
from app.models.case import EvidenceMetadata

class BaseEvidenceService(ABC):
    """Abstract base service defining the evidence storage contract for CONTINUITY."""

    @abstractmethod
    def upload_evidence(
        self,
        case_id: str,
        content: str | bytes,
        content_type: str = "text/plain",
        filename: Optional[str] = None,
        created_by: str = "system",
        description: Optional[str] = None
    ) -> EvidenceMetadata:
        """Upload raw evidence artifact and return its metadata reference."""
        pass

    @abstractmethod
    def get_evidence(self, object_key: str) -> Tuple[bytes, EvidenceMetadata]:
        """Retrieve raw evidence content and metadata by object key."""
        pass

    @abstractmethod
    def delete_evidence(self, object_key: str) -> bool:
        """Delete an evidence artifact by object key."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Lightweight storage connectivity check."""
        pass
