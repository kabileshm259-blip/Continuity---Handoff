#!/usr/bin/env python
"""Live AWS Smoke Test for DynamoDB & S3 in CONTINUITY.

Tests real DynamoDB persistence and S3 evidence storage without mocking.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure backend root is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.repositories.factory import get_repository
from app.repositories.dynamodb_repository import DynamoDBRepository
from app.evidence.factory import get_evidence_service
from app.evidence.s3_service import S3EvidenceService
from app.services.handoff_service import HandoffService
from app.services.case_service import CaseService
from app.models.case import HandoffRequest

async def run_live_smoke_test():
    print("==================================================")
    print("CONTINUITY — LIVE AWS DYNAMODB & S3 SMOKE TEST")
    print("==================================================")

    # 1. Verify Configuration
    print("\n[Step 1] Verifying Environment Configuration:")
    print(f"  AI_PROVIDER:         {os.getenv('AI_PROVIDER')}")
    print(f"  REPOSITORY_PROVIDER: {os.getenv('REPOSITORY_PROVIDER')}")
    print(f"  EVIDENCE_PROVIDER:   {os.getenv('EVIDENCE_PROVIDER')}")
    print(f"  AWS_REGION:          {os.getenv('AWS_REGION')}")
    print(f"  DYNAMODB_TABLE:      {os.getenv('DYNAMODB_TABLE')}")
    print(f"  S3_BUCKET:           {os.getenv('S3_BUCKET')}")
    print(f"  S3_PREFIX:           {os.getenv('S3_PREFIX')}")

    # 2. Verify Factory Initialization
    print("\n[Step 2] Initializing Repository & Evidence Service:")
    repo = get_repository()
    evidence_svc = get_evidence_service()

    print(f"  Repository type:     {type(repo).__name__}")
    print(f"  Evidence svc type:   {type(evidence_svc).__name__}")

    if not isinstance(repo, DynamoDBRepository):
        raise RuntimeError(f"Expected DynamoDBRepository, got {type(repo).__name__}")
    if not isinstance(evidence_svc, S3EvidenceService):
        raise RuntimeError(f"Expected S3EvidenceService, got {type(evidence_svc).__name__}")

    # 3. Check Live Connectivity
    print("\n[Step 3] Checking Live AWS Connectivity:")
    repo_health = repo.health_check()
    print(f"  DynamoDB Health:     {repo_health}")
    if repo_health.get("status") != "healthy":
        raise RuntimeError(f"DynamoDB is not healthy: {repo_health}")

    s3_health = evidence_svc.health_check()
    print(f"  S3 Health:           {s3_health}")
    if s3_health.get("status") != "healthy":
        raise RuntimeError(f"S3 is not healthy: {s3_health}")

    # 4. Perform Live Handoff
    print("\n[Step 4] Processing Live Handoff:")
    raw_notes = (
        "LIVE AWS SMOKE TEST: Replacement order handled for customer Anita. "
        "Customer sent photos of damaged packaging. "
        "Contacted logistics team; stock confirmation expected tomorrow. "
        "Promised customer update by Friday. "
        "Issue with order #9942: invoice reflects $500 discrepancy with warehouse manifest."
    )

    handoff_svc = HandoffService()
    request = HandoffRequest(
        outgoing_employee="Arun Kumar",
        incoming_employee="Priya Sharma",
        raw_notes=raw_notes,
        handoff_date="Today"
    )

    response = await handoff_svc.process_handoff(request)
    print(f"  Handoff ID:          {response.handoff_id}")
    print(f"  Cases Updated:       {response.cases_updated}")
    print(f"  Cases Created:       {response.cases_created}")

    target_case_id = response.cases_created[0] if response.cases_created else response.cases_updated[0]
    print(f"  Target Case ID:      {target_case_id}")

    # 5. Verify DynamoDB Case Persistence
    print(f"\n[Step 5] Verifying DynamoDB Persistence for {target_case_id}:")
    retrieved_case = repo.get_case(target_case_id)
    if not retrieved_case:
        raise RuntimeError(f"Case {target_case_id} not found in DynamoDB!")

    print(f"  Title:               {retrieved_case.title}")
    print(f"  Status:              {retrieved_case.status}")
    print(f"  Owner:               {retrieved_case.owner}")
    print(f"  Evidence Records:    {len(retrieved_case.evidence_records)}")

    if not retrieved_case.evidence_records:
        raise RuntimeError(f"Case {target_case_id} in DynamoDB has no evidence_records attached!")

    latest_evidence = retrieved_case.evidence_records[-1]
    print(f"  Evidence ID:         {latest_evidence.evidence_id}")
    print(f"  S3 Object Key:       {latest_evidence.object_key}")
    print(f"  Size Bytes:          {latest_evidence.size_bytes}")

    # 6. Verify S3 Object Persistence
    print(f"\n[Step 6] Verifying S3 Evidence Retrieval ({latest_evidence.object_key}):")
    content_bytes, s3_meta = evidence_svc.get_evidence(latest_evidence.object_key)
    print(f"  Retrieved from S3:   {len(content_bytes)} bytes")
    print(f"  Content Matches:     {content_bytes.decode('utf-8') == raw_notes}")
    if content_bytes.decode("utf-8") != raw_notes:
        raise RuntimeError("S3 content does not match original raw handoff notes!")

    # 7. Verify Audit Event
    print(f"\n[Step 7] Verifying Audit Trail in DynamoDB:")
    evidence_events = [e for e in retrieved_case.audit_history if e.action == "EVIDENCE_CREATED"]
    print(f"  EVIDENCE_CREATED events: {len(evidence_events)}")
    if not evidence_events:
        raise RuntimeError("No EVIDENCE_CREATED audit event found in case history!")
    print(f"  Latest Audit Event:  [{evidence_events[-1].timestamp}] {evidence_events[-1].action} -> {evidence_events[-1].details}")

    # 8. Verify Queue Query from DynamoDB
    print("\n[Step 8] Verifying CaseService Queue Query against DynamoDB:")
    case_svc = CaseService()
    queue = case_svc.get_queue()
    print(f"  Total Cases in Queue: {queue.stats.total}")
    print(f"  Unresolved:           {queue.stats.unresolved}")
    print(f"  At Risk:              {queue.stats.at_risk}")
    print(f"  Blocked:              {queue.stats.blocked}")
    print(f"  Exceptions:           {queue.stats.exceptions}")

    print("\n==================================================")
    print("SUCCESS: REAL AWS DYNAMODB & S3 VERIFIED END-TO-END!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_live_smoke_test())
