import os
import uuid
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from app.evidence.base import BaseEvidenceService
from app.models.case import EvidenceMetadata

logger = logging.getLogger("continuity.s3")

class S3EvidenceService(BaseEvidenceService):
    """Amazon S3 implementation for durable workplace handoff evidence storage.
    
    Uses standard AWS credential chain via boto3 and operates on a private S3 bucket.
    """

    def __init__(
        self,
        bucket: Optional[str] = None,
        prefix: Optional[str] = None,
        region: Optional[str] = None,
        client: Optional[Any] = None
    ):
        self.bucket = bucket or os.getenv("S3_BUCKET", "continuity-evidence-dev")
        self.prefix = prefix or os.getenv("S3_PREFIX", "cases")
        self.region = region or os.getenv("AWS_REGION", "ap-south-1")
        self._client = client

    def _get_client(self):
        """Lazy-initialize boto3 S3 client using standard credential provider chain."""
        if self._client is not None:
            return self._client

        try:
            import boto3
            if self.region:
                os.environ.setdefault("AWS_DEFAULT_REGION", self.region)
            session = boto3.Session(region_name=self.region)
            self._client = session.client("s3", region_name=self.region)
            return self._client
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise RuntimeError(f"S3 connection error for bucket '{self.bucket}': {str(e)}")

    def upload_evidence(
        self,
        case_id: str,
        content: str | bytes,
        content_type: str = "text/plain",
        filename: Optional[str] = None,
        created_by: str = "system",
        description: Optional[str] = None
    ) -> EvidenceMetadata:
        client = self._get_client()
        evidence_id = f"EVD-{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content_bytes = content.encode("utf-8") if isinstance(content, str) else content
        # Predictable, sanitized object key structure: cases/{case_id}/evidence/{evidence_id}.txt
        object_key = f"{self.prefix}/{case_id}/evidence/{evidence_id}.txt"

        s3_metadata = {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "created_by": created_by
        }
        if filename:
            s3_metadata["original_filename"] = filename

        try:
            client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=content_bytes,
                ContentType=content_type,
                Metadata=s3_metadata
            )
        except Exception as e:
            logger.error(f"Failed to upload evidence to S3 bucket '{self.bucket}': {e}")
            raise RuntimeError(f"Failed to persist evidence to S3: {str(e)}")

        return EvidenceMetadata(
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

    def get_evidence(self, object_key: str) -> Tuple[bytes, EvidenceMetadata]:
        client = self._get_client()
        try:
            response = client.get_object(Bucket=self.bucket, Key=object_key)
            content_bytes = response["Body"].read()
            s3_metadata = response.get("Metadata", {})
            content_type = response.get("ContentType", "text/plain")
            content_length = response.get("ContentLength", len(content_bytes))

            metadata = EvidenceMetadata(
                evidence_id=s3_metadata.get("evidence_id", "UNKNOWN"),
                case_id=s3_metadata.get("case_id", "UNKNOWN"),
                object_key=object_key,
                content_type=content_type,
                original_filename=s3_metadata.get("original_filename"),
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                created_by=s3_metadata.get("created_by", "system"),
                size_bytes=content_length
            )
            return (content_bytes, metadata)
        except Exception as e:
            logger.error(f"Failed to get evidence object '{object_key}' from S3: {e}")
            raise RuntimeError(f"Failed to retrieve evidence from S3: {str(e)}")

    def delete_evidence(self, object_key: str) -> bool:
        client = self._get_client()
        try:
            client.delete_object(Bucket=self.bucket, Key=object_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete evidence object '{object_key}' from S3: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Lightweight head_bucket check without failing health check if S3 is unreachable."""
        try:
            client = self._get_client()
            client.head_bucket(Bucket=self.bucket)
            return {
                "provider": "s3",
                "status": "healthy",
                "bucket": self.bucket,
                "region": self.region,
                "prefix": self.prefix
            }
        except Exception as e:
            logger.warning(f"S3 health check warning for bucket '{self.bucket}': {e}")
            return {
                "provider": "s3",
                "status": "degraded",
                "bucket": self.bucket,
                "region": self.region,
                "error": str(e)
            }
