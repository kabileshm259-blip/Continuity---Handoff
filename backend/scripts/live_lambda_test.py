#!/usr/bin/env python
"""Controlled Live AWS Test for Deployed Lambda (continuity-deadline-evaluator).

Tests the deployed Lambda function in ap-south-1 against real DynamoDB cases:
1. Creates 3 temporary cases:
   - Future deadline: should remain UNRESOLVED (unchanged).
   - Expired deadline: should transition to OVERDUE with URGENT priority.
   - Approaching deadline + blocker: should transition to AT_RISK with HIGH priority.
2. Invokes deployed Lambda: continuity-deadline-evaluator.
3. Verifies state transitions and audit events in DynamoDB.
4. Invokes deployed Lambda second time to verify strict idempotency (changed=0, 0 duplicate audits).
5. Cleans up only the 3 temporary test cases.
"""
import os
import sys
import json
import uuid
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

import boto3
from app.repositories.factory import get_repository
from app.models.case import Case, Blocker, AuditEvent
from app.models.enums import CaseStatus, Priority, BlockerStatus

def run_controlled_lambda_test():
    print("==================================================")
    print("CONTINUITY — DEPLOYED LAMBDA CONTROLLED LIVE TEST")
    print("==================================================")

    repo = get_repository()
    now_utc = datetime.now(timezone.utc)
    test_run_id = uuid.uuid4().hex[:6].upper()

    case_future_id = f"CASE-TMP-FUT-{test_run_id}"
    case_expired_id = f"CASE-TMP-EXP-{test_run_id}"
    case_risk_id = f"CASE-TMP-RSK-{test_run_id}"

    dt_future = (now_utc + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M:%SZ")
    dt_expired = (now_utc - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    dt_approaching = (now_utc + timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")

    print("\n[Step 1] Creating 3 Temporary Controlled Test Cases:")
    print(f"  Case 1 (Future):      {case_future_id} | Deadline: {dt_future}")
    print(f"  Case 2 (Expired):     {case_expired_id} | Deadline: {dt_expired}")
    print(f"  Case 3 (Approaching): {case_risk_id} | Deadline: {dt_approaching} (with active blocker)")

    case_future = Case(
        case_id=case_future_id,
        title="CONTROLLED TEST: Future deadline task",
        owner="Priya Sharma",
        status=CaseStatus.UNRESOLVED,
        priority=Priority.MEDIUM,
        deadline=dt_future,
        created_at=now_utc.isoformat(),
        updated_at=now_utc.isoformat(),
        audit_history=[
            AuditEvent(event_id="EVT-1", case_id=case_future_id, timestamp=now_utc.isoformat(), actor="TestSetup", action="CREATED", details="Future case")
        ]
    )

    case_expired = Case(
        case_id=case_expired_id,
        title="CONTROLLED TEST: Expired deadline task",
        owner="Priya Sharma",
        status=CaseStatus.UNRESOLVED,
        priority=Priority.MEDIUM,
        deadline=dt_expired,
        created_at=now_utc.isoformat(),
        updated_at=now_utc.isoformat(),
        audit_history=[
            AuditEvent(event_id="EVT-2", case_id=case_expired_id, timestamp=now_utc.isoformat(), actor="TestSetup", action="CREATED", details="Expired case")
        ]
    )

    case_risk = Case(
        case_id=case_risk_id,
        title="CONTROLLED TEST: Approaching deadline with blocker",
        owner="Priya Sharma",
        status=CaseStatus.UNRESOLVED,
        priority=Priority.MEDIUM,
        deadline=dt_approaching,
        created_at=now_utc.isoformat(),
        updated_at=now_utc.isoformat(),
        blockers=[
            Blocker(
                blocker_id=f"BLK-{test_run_id}",
                case_id=case_risk_id,
                description="Waiting on tier-3 engineering approval",
                blocked_by="DevOps",
                status=BlockerStatus.ACTIVE
            )
        ],
        audit_history=[
            AuditEvent(event_id="EVT-3", case_id=case_risk_id, timestamp=now_utc.isoformat(), actor="TestSetup", action="CREATED", details="Approaching risk case")
        ]
    )

    repo.save_case(case_future)
    repo.save_case(case_expired)
    repo.save_case(case_risk)
    print("  All 3 test cases persisted to DynamoDB.")

    # 2. Invoke Deployed Lambda Function
    print("\n[Step 2] Invoking Deployed Lambda Function (continuity-deadline-evaluator):")
    lambda_client = boto3.client("lambda", region_name="ap-south-1")
    resp = lambda_client.invoke(
        FunctionName="continuity-deadline-evaluator",
        InvocationType="RequestResponse",
        Payload=json.dumps({"source": "controlled-live-test"}).encode("utf-8")
    )
    payload1 = json.loads(resp["Payload"].read().decode("utf-8"))
    print(f"  Lambda Status Code: {payload1.get('statusCode')}")
    body1 = payload1.get("body", {})
    print(f"  Lambda Summary:     {body1}")

    # 3. Verify Transitions in DynamoDB
    print("\n[Step 3] Verifying Transitions in DynamoDB:")
    c_fut = repo.get_case(case_future_id)
    c_exp = repo.get_case(case_expired_id)
    c_rsk = repo.get_case(case_risk_id)

    print(f"  Case Future:      Status={c_fut.status} (Expected: UNRESOLVED)")
    print(f"  Case Expired:     Status={c_exp.status} | Priority={c_exp.priority} (Expected: OVERDUE / URGENT)")
    print(f"  Case Approaching: Status={c_rsk.status} | Priority={c_rsk.priority} (Expected: AT_RISK / HIGH)")

    assert c_fut.status == CaseStatus.UNRESOLVED, f"Expected UNRESOLVED, got {c_fut.status}"
    assert c_exp.status == CaseStatus.OVERDUE, f"Expected OVERDUE, got {c_exp.status}"
    assert c_exp.priority == Priority.URGENT, f"Expected URGENT, got {c_exp.priority}"
    assert c_rsk.status == CaseStatus.AT_RISK, f"Expected AT_RISK, got {c_rsk.status}"
    assert c_rsk.priority == Priority.HIGH, f"Expected HIGH, got {c_rsk.priority}"

    # Verify audit events
    audit_exp = c_exp.audit_history[-1]
    audit_rsk = c_rsk.audit_history[-1]
    print(f"  Expired Audit:    [{audit_exp.timestamp}] {audit_exp.action} by {audit_exp.actor} -> {audit_exp.details}")
    print(f"  At Risk Audit:    [{audit_rsk.timestamp}] {audit_rsk.action} by {audit_rsk.actor} -> {audit_rsk.details}")

    assert audit_exp.action == "CASE_STATUS_CHANGED" and audit_exp.actor == "SYSTEM"
    assert audit_rsk.action == "CASE_STATUS_CHANGED" and audit_rsk.actor == "SYSTEM"

    # 4. Second Invocation (Idempotency Check)
    print("\n[Step 4] Invoking Deployed Lambda Second Time (Idempotency Check):")
    resp2 = lambda_client.invoke(
        FunctionName="continuity-deadline-evaluator",
        InvocationType="RequestResponse",
        Payload=json.dumps({"source": "controlled-live-test-run-2"}).encode("utf-8")
    )
    payload2 = json.loads(resp2["Payload"].read().decode("utf-8"))
    body2 = payload2.get("body", {})
    print(f"  Lambda Summary Run 2: {body2}")
    assert body2.get("changed") == 0, f"Expected changed=0 on run 2, got {body2.get('changed')}"

    c_exp2 = repo.get_case(case_expired_id)
    assert len(c_exp2.audit_history) == len(c_exp.audit_history), "Audit count increased on rerun!"
    print("  IDEMPOTENCY CONFIRMED: 0 duplicate transitions and 0 duplicate audit events.")

    # 5. Cleanup
    print("\n[Step 5] Cleaning Up Temporary Test Cases:")
    table = repo._get_table()
    table.delete_item(Key={"case_id": case_future_id})
    table.delete_item(Key={"case_id": case_expired_id})
    table.delete_item(Key={"case_id": case_risk_id})
    print(f"  Cleaned up {case_future_id}, {case_expired_id}, {case_risk_id} from DynamoDB.")

    print("\n==================================================")
    print("SUCCESS: DEPLOYED LAMBDA VERIFIED END-TO-END!")
    print("==================================================")

if __name__ == "__main__":
    run_controlled_lambda_test()
