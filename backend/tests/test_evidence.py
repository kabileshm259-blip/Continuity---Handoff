import os
import unittest
import asyncio
from io import BytesIO
from unittest.mock import MagicMock, patch

from app.models.case import EvidenceMetadata, HandoffRequest, Case
from app.evidence.base import BaseEvidenceService
from app.evidence.memory_service import MemoryEvidenceService
from app.evidence.s3_service import S3EvidenceService
from app.evidence.factory import get_evidence_service, reset_evidence_service
from app.services.handoff_service import HandoffService
from app.repositories.factory import reset_repository_instance

class TestEvidenceStorage(unittest.TestCase):

    def setUp(self):
        reset_evidence_service()
        reset_repository_instance()

    def tearDown(self):
        reset_evidence_service()
        reset_repository_instance()

    def test_1_evidence_metadata_model(self):
        """1. EvidenceMetadata model validates fields and defaults properly."""
        meta = EvidenceMetadata(
            evidence_id="EVD-001",
            case_id="CASE-1042",
            object_key="cases/CASE-1042/evidence/EVD-001.txt",
            created_at="2026-09-20 12:00:00",
            size_bytes=150
        )
        self.assertEqual(meta.evidence_id, "EVD-001")
        self.assertEqual(meta.content_type, "text/plain")
        self.assertEqual(meta.created_by, "system")
        self.assertEqual(meta.size_bytes, 150)

    def test_2_memory_evidence_service_crud(self):
        """2. MemoryEvidenceService uploads, retrieves, and deletes evidence in memory."""
        service = MemoryEvidenceService()
        
        # Upload
        meta = service.upload_evidence(
            case_id="CASE-1042",
            content="Customer sent damaged product photos.",
            content_type="text/plain",
            filename="notes.txt",
            created_by="Arun Kumar"
        )
        self.assertEqual(meta.case_id, "CASE-1042")
        self.assertTrue(meta.object_key.startswith("cases/CASE-1042/evidence/"))
        self.assertEqual(meta.created_by, "Arun Kumar")
        self.assertGreater(meta.size_bytes, 0)

        # Retrieve
        content, retrieved_meta = service.get_evidence(meta.object_key)
        self.assertEqual(content.decode("utf-8"), "Customer sent damaged product photos.")
        self.assertEqual(retrieved_meta.evidence_id, meta.evidence_id)

        # Health check
        health = service.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["provider"], "memory")
        self.assertEqual(health["total_items"], 1)

        # Delete
        self.assertTrue(service.delete_evidence(meta.object_key))
        with self.assertRaises(KeyError):
            service.get_evidence(meta.object_key)

    def test_3_s3_evidence_service_with_mocked_boto3(self):
        """3. S3EvidenceService uploads, retrieves, and deletes using mocked boto3 S3 client."""
        mock_s3 = MagicMock()
        service = S3EvidenceService(
            bucket="continuity-evidence-test",
            prefix="cases",
            region="ap-south-1",
            client=mock_s3
        )

        # Upload test
        meta = service.upload_evidence(
            case_id="CASE-1038",
            content="Invoice correction raw email text.",
            created_by="Arun Kumar",
            filename="invoice.txt"
        )
        self.assertEqual(meta.case_id, "CASE-1038")
        self.assertTrue(meta.object_key.startswith("cases/CASE-1038/evidence/"))
        mock_s3.put_object.assert_called_once()
        put_kwargs = mock_s3.put_object.call_args[1]
        self.assertEqual(put_kwargs["Bucket"], "continuity-evidence-test")
        self.assertEqual(put_kwargs["Key"], meta.object_key)
        self.assertEqual(put_kwargs["ContentType"], "text/plain")
        self.assertEqual(put_kwargs["Metadata"]["case_id"], "CASE-1038")

        # Get test
        mock_s3.get_object.return_value = {
            "Body": BytesIO(b"Invoice correction raw email text."),
            "Metadata": {"case_id": "CASE-1038", "evidence_id": meta.evidence_id, "created_by": "Arun Kumar"},
            "ContentType": "text/plain",
            "ContentLength": 34
        }
        content_bytes, retrieved_meta = service.get_evidence(meta.object_key)
        self.assertEqual(content_bytes, b"Invoice correction raw email text.")
        self.assertEqual(retrieved_meta.case_id, "CASE-1038")

        # Delete test
        self.assertTrue(service.delete_evidence(meta.object_key))
        mock_s3.delete_object.assert_called_once_with(
            Bucket="continuity-evidence-test",
            Key=meta.object_key
        )

        # Health check test
        health = service.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["provider"], "s3")
        mock_s3.head_bucket.assert_called_once_with(Bucket="continuity-evidence-test")

    def test_4_evidence_factory_selection(self):
        """4. get_evidence_service() selects MemoryEvidenceService by default and S3EvidenceService when configured."""
        with patch.dict(os.environ, {"EVIDENCE_PROVIDER": "memory"}):
            reset_evidence_service()
            self.assertIsInstance(get_evidence_service(), MemoryEvidenceService)

        with patch.dict(os.environ, {"EVIDENCE_PROVIDER": ""}):
            reset_evidence_service()
            self.assertIsInstance(get_evidence_service(), MemoryEvidenceService)

        with patch.dict(os.environ, {"EVIDENCE_PROVIDER": "s3"}):
            reset_evidence_service()
            self.assertIsInstance(get_evidence_service(), S3EvidenceService)

    def test_5_handoff_creates_evidence_and_audit_event(self):
        """5. Handoff flow creates evidence record and attaches EVIDENCE_CREATED audit event."""
        service = HandoffService()
        
        request = HandoffRequest(
            outgoing_employee="Arun Kumar",
            incoming_employee="Priya Sharma",
            raw_notes="Replacement request handled. Customer sent damaged product photos yesterday.",
            handoff_date="Today"
        )
        
        response = asyncio.run(service.process_handoff(request))
        self.assertGreater(len(response.cases_updated), 0)

        # Verify case has evidence_records attached
        case_1042 = service.repo.get_case("CASE-1042")
        self.assertIsNotNone(case_1042)
        self.assertGreater(len(case_1042.evidence_records), 0)
        
        latest_evidence = case_1042.evidence_records[-1]
        self.assertTrue(latest_evidence.object_key.startswith("cases/CASE-1042/evidence/"))
        self.assertEqual(latest_evidence.created_by, "Arun Kumar")

        # Verify EVIDENCE_CREATED audit event was logged with safe metadata
        evidence_events = [e for e in case_1042.audit_history if e.action == "EVIDENCE_CREATED"]
        self.assertGreater(len(evidence_events), 0)
        self.assertIn("Raw handoff notes archived", evidence_events[-1].details)
        self.assertIn(latest_evidence.evidence_id, evidence_events[-1].details)

    def test_6_optional_live_s3_smoke_test(self):
        """6. Optional live S3 smoke test (only runs when RUN_LIVE_S3_TEST=true)."""
        if os.getenv("RUN_LIVE_S3_TEST", "false").lower() != "true":
            self.skipTest("Live S3 test skipped (RUN_LIVE_S3_TEST not set).")

        service = S3EvidenceService()
        health = service.health_check()
        self.assertEqual(health.get("status"), "healthy")

if __name__ == "__main__":
    unittest.main()
