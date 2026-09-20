import uuid
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from app.evidence.base import BaseEvidenceService
from app.models.case import EvidenceMetadata

class MemoryEvidenceService(BaseEvidenceService):
    """In-memory evidence storage service for local development and testing."""

    def __init__(self):
        # Maps object_key -> (content_bytes, EvidenceMetadata)
        self._store: Dict[str, Tuple[bytes, EvidenceMetadata]] = {}

    def upload_evidence(
        self,
        case_id: str,
        content: str | bytes,
        content_type: str = "text/plain",
        filename: Optional[str] = None,
        created_by: str = "system",
        description: Optional[str] = None
    ) -> EvidenceMetadata:
        evidence_id = f"EVD-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        object_key = f"cases/{case_id}/evidence/{evidence_id}.txt"

        metadata = EvidenceMetadata(
            evidence_id=evidence_id,
            case_id=case_id,
            object_key=object_key,
            content_type=content_type,
            original_filename=filename,
            created_at=now_str,
            created_by=created_by,
            size_bytes=len(content_bytes),
            description=description
        )

        self._store[object_key] = (content_bytes, metadata)
        return metadata

    def get_evidence(self, object_key: str) -> Tuple[bytes, EvidenceMetadata]:
        if object_key not in self._store:
            raise KeyError(f"Evidence not found at object key: '{object_key}'")
        return self._store[object_key]

    def delete_evidence(self, object_key: str) -> bool:
        if object_key in self._store:
            del self._store[object_key]
            return True
        return False

    def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "memory",
            "status": "healthy",
            "total_items": len(self._store)
        }
