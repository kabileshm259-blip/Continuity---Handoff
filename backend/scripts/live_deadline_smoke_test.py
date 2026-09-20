#!/usr/bin/env python
"""Live AWS Smoke Test for Time & Continuity Enforcement (Phase 5).

Tests real DynamoDB persistence and deadline evaluation against continuity-cases-dev in ap-south-1.
Verifies:
1. Case persistence in DynamoDB.
2. Evaluator reads case from DynamoDB.
3. Deterministic deadline evaluation against UTC.
4. Status transition to OVERDUE with URGENT priority.
5. CASE_STATUS_CHANGED audit event persisted with actor='SYSTEM'.
6. Re-running evaluation is strictly idempotent (0 duplicate transitions, 0 duplicate audit events).
"""
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.repositories.factory import get_repository
from app.repositories.dynamodb_repository import DynamoDBRepository
from app.services.deadline_service import DeadlineEvaluationService
from app.models.case import Case, AuditEvent
from app.models.enums import CaseStatus, Priority

def run_live_deadline_smoke_test():
    print("==================================================")
    print("CONTINUITY — LIVE AWS DEADLINE ENFORCEMENT SMOKE TEST")
    print("==================================================")

    # 1. Verify Configuration & DynamoDB Connectivity
    print("\n[Step 1] Verifying DynamoDB Configuration & Connectivity:")
    repo = get_repository()
    print(f"  Repository type: {type(repo).__name__}")
    if not isinstance(repo, DynamoDBRepository):
        raise RuntimeError(f"Expected DynamoDBRepository, got {type(repo).__name__}")

    health = repo.health_check()
    print(f"  DynamoDB Health: {health}")
    if health.get("status") != "healthy":
        raise RuntimeError(f"DynamoDB is not healthy: {health}")

    # 2. Create a Controlled Test Case with Passed Deadline
    test_case_id = f"CASE-DEADLINE-{uuid.uuid4().hex[:6].upper()}"
    now_utc = datetime.now(timezone.utc)
    passed_deadline = (now_utc - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"\n[Step 2] Creating Controlled Test Case ({test_case_id}):")
    print(f"  Initial Status:   {CaseStatus.UNRESOLVED}")
    print(f"  Initial Priority: {Priority.MEDIUM}")
    print(f"  Target Deadline:  {passed_deadline} (Passed 2 hours ago)")

    test_case = Case(
        case_id=test_case_id,
        title="SMOKE TEST: Hardware replacement deadline verification",
        description="Controlled test case created to verify automated deadline evaluation and idempotency.",
        owner="Priya Sharma",
        status=CaseStatus.UNRESOLVED,
        priority=Priority.MEDIUM,
        deadline=passed_deadline,
        created_at=now_utc.isoformat(),
        updated_at=now_utc.isoformat(),
        audit_history=[
            AuditEvent(
                event_id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                case_id=test_case_id,
                timestamp=now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                actor="SmokeTestSetup",
                action="CASE_CREATED",
                details="Test case initialized with UNRESOLVED status."
            )
        ]
    )

    repo.save_case(test_case)
    print(f"  Saved {test_case_id} to DynamoDB table '{repo.table_name}'.")

    # 3. Verify Case Exists in DynamoDB
    print(f"\n[Step 3] Verifying Case Exists in DynamoDB:")
    persisted_case = repo.get_case(test_case_id)
    if not persisted_case:
        raise RuntimeError(f"Test case {test_case_id} not found in DynamoDB!")
    print(f"  Found case: {persisted_case.case_id} | Status: {persisted_case.status} | Deadline: {persisted_case.deadline}")
    initial_audit_count = len(persisted_case.audit_history)

    # 4. Run Deadline Evaluation (First Run)
    print(f"\n[Step 4] Running DeadlineEvaluationService (First Run):")
    service = DeadlineEvaluationService(repo=repo)
    summary1 = service.evaluate_all_cases()
    print(f"  Evaluated: {summary1.evaluated}")
    print(f"  Changed:   {summary1.changed}")
    print(f"  Overdue:   {summary1.overdue}")
    print(f"  At Risk:   {summary1.at_risk}")
    print(f"  Unchanged: {summary1.unchanged}")

    # 5. Verify Case Transitioned in DynamoDB
    print(f"\n[Step 5] Verifying State Transition in DynamoDB:")
    updated_case = repo.get_case(test_case_id)
    print(f"  New Status:   {updated_case.status}")
    print(f"  New Priority: {updated_case.priority}")
    print(f"  Audit Count:  {len(updated_case.audit_history)} (was {initial_audit_count})")

    if updated_case.status != CaseStatus.OVERDUE:
        raise RuntimeError(f"Expected status {CaseStatus.OVERDUE}, got {updated_case.status}")
    if updated_case.priority != Priority.URGENT:
        raise RuntimeError(f"Expected priority {Priority.URGENT}, got {updated_case.priority}")

    latest_audit = updated_case.audit_history[-1]
    print(f"  Latest Audit: [{latest_audit.timestamp}] {latest_audit.action} by {latest_audit.actor}")
    print(f"  Audit Detail: {latest_audit.details}")

    if latest_audit.action != "CASE_STATUS_CHANGED":
        raise RuntimeError(f"Expected action 'CASE_STATUS_CHANGED', got {latest_audit.action}")
    if latest_audit.actor != "SYSTEM":
        raise RuntimeError(f"Expected actor 'SYSTEM', got {latest_audit.actor}")
    if "OVERDUE" not in latest_audit.details:
        raise RuntimeError("Audit details do not reference OVERDUE transition!")

    # 6. Verify Idempotency (Second Run)
    print(f"\n[Step 6] Verifying Idempotency (Second Run):")
    summary2 = service.evaluate_all_cases()
    print(f"  Evaluated: {summary2.evaluated}")
    print(f"  Changed:   {summary2.changed} (must be 0 for this test case)")
    print(f"  Unchanged: {summary2.unchanged}")

    rechecked_case = repo.get_case(test_case_id)
    if len(rechecked_case.audit_history) != len(updated_case.audit_history):
        raise RuntimeError(
            f"Idempotency failed: audit history increased from "
            f"{len(updated_case.audit_history)} to {len(rechecked_case.audit_history)}"
        )
    print("  IDEMPOTENCY CONFIRMED: 0 duplicate transitions and 0 duplicate audit events.")

    # 7. Clean up the Smoke Test Case from DynamoDB
    print(f"\n[Step 7] Cleaning Up Smoke Test Case:")
    try:
        repo._get_table().delete_item(Key={"case_id": test_case_id})
        print(f"  Deleted test item {test_case_id} from DynamoDB.")
    except Exception as e:
        print(f"  Warning: could not delete test item: {e}")

    print("\n==================================================")
    print("SUCCESS: REAL AWS DEADLINE ENFORCEMENT VERIFIED!")
    print("==================================================")

if __name__ == "__main__":
    run_live_deadline_smoke_test()
