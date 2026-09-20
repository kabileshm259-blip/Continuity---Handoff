import os
from typing import Optional
from app.evidence.base import BaseEvidenceService
from app.evidence.memory_service import MemoryEvidenceService
from app.evidence.s3_service import S3EvidenceService

_evidence_service_instance: Optional[BaseEvidenceService] = None

def get_evidence_service() -> BaseEvidenceService:
    """Factory to retrieve configured evidence storage service based on EVIDENCE_PROVIDER.
    
    Options:
    - 'memory' (default): In-memory storage for local development and unit tests.
    - 's3': Real Amazon S3 evidence storage using standard AWS credential chain.
    """
    global _evidence_service_instance
    if _evidence_service_instance is not None:
        return _evidence_service_instance

    provider = os.getenv("EVIDENCE_PROVIDER", "memory").strip().lower()

    if provider == "s3":
        _evidence_service_instance = S3EvidenceService()
    else:
        _evidence_service_instance = MemoryEvidenceService()

    return _evidence_service_instance

def reset_evidence_service():
    """Reset evidence service singleton (useful for testing)."""
    global _evidence_service_instance
    _evidence_service_instance = None
