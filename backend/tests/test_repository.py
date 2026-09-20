import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.repositories.base import BaseRepository
from app.repositories.memory_repository import InMemoryRepository
from app.repositories.dynamodb_repository import DynamoDBRepository
from app.repositories.factory import get_repository, reset_repository_instance
from app.models.case import Case, Handoff, AuditEvent, TaskItem, Commitment, Blocker, ExceptionItem
from app.models.enums import CaseStatus, Priority, WorkItemStatus, CommitmentStatus, BlockerStatus, ExceptionStatus

class TestRepositoryLayer(unittest.TestCase):

    def setUp(self):
        reset_repository_instance()

    def tearDown(self):
        reset_repository_instance()

    def _create_sample_case(self, case_id="CASE-TEST-1") -> Case:
        return Case(
            case_id=case_id,
            title="Test Case Title",
            description="Testing case description",
            owner="Arun Kumar",
            status=CaseStatus.UNRESOLVED,
            priority=Priority.HIGH,
            deadline="Tomorrow",
            customer="Acme Corp",
            created_at="Today, 10:00 AM",
            updated_at="Today, 10:00 AM",
            next_action="Follow up with warehouse",
            tasks=[
                TaskItem(task_id="TASK-1", case_id=case_id, title="Check stock", status=WorkItemStatus.PENDING)
            ],
            commitments=[
                Commitment(commitment_id="COM-1", case_id=case_id, description="Deliver by Friday", committed_to="Acme", expected_date="Friday")
            ],
            blockers=[
                Blocker(blocker_id="BLK-1", case_id=case_id, description="Awaiting stock", blocked_by="Warehouse")
            ],
            exceptions=[],
            audit_history=[
                AuditEvent(event_id="EVT-1", case_id=case_id, timestamp="10:00 AM", actor="Arun", action="Created", details="Initial intake")
            ]
        )

    def test_1_base_repository_interface_cannot_be_instantiated(self):
        """1. BaseRepository is an abstract class and cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            BaseRepository()

    def test_2_in_memory_repository_crud_and_audit(self):
        """2. InMemoryRepository performs case CRUD, handoff storage, and audit appending."""
        repo = InMemoryRepository(seed=False)
        self.assertEqual(len(repo.get_all_cases()), 0)

        # Create case
        sample = self._create_sample_case("CASE-MEM-1")
        saved = repo.save_case(sample)
        self.assertEqual(saved.case_id, "CASE-MEM-1")

        # Retrieve case
        retrieved = repo.get_case("CASE-MEM-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.title, "Test Case Title")

        # Add audit event
        event = repo.add_audit_event("CASE-MEM-1", actor="Priya Sharma", action="Assigned", details="Assigned to Priya")
        self.assertIsNotNone(event)
        self.assertEqual(event.actor, "Priya Sharma")
        
        # Verify audit history updated
        updated_case = repo.get_case("CASE-MEM-1")
        self.assertEqual(len(updated_case.audit_history), 2)
        self.assertEqual(updated_case.audit_history[-1].action, "Assigned")

        # Save and get handoff
        handoff = Handoff(
            handoff_id="HND-MEM-1",
            outgoing_employee="Arun Kumar",
            incoming_employee="Priya Sharma",
            raw_notes="Sample handoff notes",
            created_at="Today, 10:00 AM"
        )
        repo.save_handoff(handoff)
        retrieved_handoff = repo.get_handoff("HND-MEM-1")
        self.assertIsNotNone(retrieved_handoff)
        self.assertEqual(retrieved_handoff.outgoing_employee, "Arun Kumar")

        # Health check
        health = repo.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["provider"], "memory")

    def test_3_dynamodb_repository_with_mocked_boto3(self):
        """3. DynamoDBRepository persists cases and handoffs using mocked boto3 Table resource."""
        mock_table = MagicMock()
        repo = DynamoDBRepository(table_name="test-table", region="ap-south-1", table_resource=mock_table)

        sample = self._create_sample_case("CASE-DYN-1")
        sample_dict = sample.model_dump()
        sample_dict["item_type"] = "CASE"

        handoff_dict = {
            "case_id": "HANDOFF#HND-1",
            "handoff_id": "HND-1",
            "outgoing_employee": "Arun Kumar",
            "incoming_employee": "Priya Sharma",
            "raw_notes": "Sample notes",
            "created_at": "Today",
            "item_type": "HANDOFF"
        }

        # Test scan (get_all_cases) - should filter out handoff items
        mock_table.scan.return_value = {"Items": [sample_dict, handoff_dict]}
        cases = repo.get_all_cases()
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0].case_id, "CASE-DYN-1")

        # Test get_case
        mock_table.get_item.return_value = {"Item": sample_dict}
        case = repo.get_case("CASE-DYN-1")
        self.assertIsNotNone(case)
        self.assertEqual(case.customer, "Acme Corp")
        mock_table.get_item.assert_called_with(Key={"case_id": "CASE-DYN-1"})

        # Test save_case
        repo.save_case(sample)
        mock_table.put_item.assert_called()
        put_call_args = mock_table.put_item.call_args[1]["Item"]
        self.assertEqual(put_call_args["case_id"], "CASE-DYN-1")
        self.assertEqual(put_call_args["item_type"], "CASE")

        # Test save_handoff
        handoff = Handoff(
            handoff_id="HND-DYN-1",
            outgoing_employee="Arun Kumar",
            incoming_employee="Priya Sharma",
            raw_notes="DynamoDB handoff",
            created_at="Today"
        )
        repo.save_handoff(handoff)
        handoff_call_args = mock_table.put_item.call_args[1]["Item"]
        self.assertEqual(handoff_call_args["case_id"], "HANDOFF#HND-DYN-1")
        self.assertEqual(handoff_call_args["item_type"], "HANDOFF")

        # Test get_handoff
        mock_table.get_item.return_value = {
            "Item": {
                "case_id": "HANDOFF#HND-DYN-1",
                "handoff_id": "HND-DYN-1",
                "outgoing_employee": "Arun Kumar",
                "incoming_employee": "Priya Sharma",
                "raw_notes": "DynamoDB handoff",
                "created_at": "Today",
                "item_type": "HANDOFF"
            }
        }
        retrieved_hnd = repo.get_handoff("HND-DYN-1")
        self.assertIsNotNone(retrieved_hnd)
        self.assertEqual(retrieved_hnd.handoff_id, "HND-DYN-1")

        # Test health check
        mock_table.table_status = "ACTIVE"
        mock_table.item_count = 5
        health = repo.health_check()
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["provider"], "dynamodb")
        self.assertEqual(health["table_status"], "ACTIVE")

    def test_4_repository_factory_selection(self):
        """4. get_repository() selects InMemoryRepository by default and DynamoDBRepository when configured."""
        with patch.dict(os.environ, {"REPOSITORY_PROVIDER": "memory"}):
            reset_repository_instance()
            repo = get_repository()
            self.assertIsInstance(repo, InMemoryRepository)

        with patch.dict(os.environ, {"REPOSITORY_PROVIDER": ""}):
            reset_repository_instance()
            repo = get_repository()
            self.assertIsInstance(repo, InMemoryRepository)

        with patch.dict(os.environ, {"REPOSITORY_PROVIDER": "dynamodb"}):
            reset_repository_instance()
            repo = get_repository()
            self.assertIsInstance(repo, DynamoDBRepository)

    def test_5_optional_live_dynamodb_smoke_test(self):
        """5. Optional live DynamoDB smoke test (only runs when RUN_LIVE_DYNAMODB_TEST=true)."""
        if os.getenv("RUN_LIVE_DYNAMODB_TEST", "false").lower() != "true":
            self.skipTest("Live DynamoDB test skipped (RUN_LIVE_DYNAMODB_TEST not set).")

        repo = DynamoDBRepository()
        health = repo.health_check()
        self.assertEqual(health.get("status"), "healthy")

if __name__ == "__main__":
    unittest.main()
