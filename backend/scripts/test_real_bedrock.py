#!/usr/bin/env python
"""Focused integration test for REAL Amazon Bedrock AI extraction in CONTINUITY.

Tests model: global.amazon.nova-2-lite-v1:0 via Bedrock Runtime Converse API.
Uses the realistic workplace handoff text.
"""
import os
import sys
import json
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.ai.bedrock_provider import BedrockAIProvider
from app.models.ai_extraction import AIExtractionResult

async def test_bedrock_extraction():
    print("==================================================")
    print("CONTINUITY — REAL AMAZON BEDROCK NOVA 2 LITE TEST")
    print("==================================================")

    model_id = os.getenv("BEDROCK_MODEL_ID", "global.amazon.nova-2-lite-v1:0")
    region = os.getenv("AWS_REGION", "ap-south-1")

    print(f"Target Region:   {region}")
    print(f"Target Model ID: {model_id}\n")

    raw_notes = (
        "Payment API integration is complete. Webhook handling is still pending. "
        "Finance has not approved the discount yet. I promised the client the revised version before Friday. "
        "Follow up with Finance and finish webhook validation."
    )

    print("Input Messy Handoff Notes:")
    print("-" * 50)
    print(raw_notes)
    print("-" * 50)

    provider = BedrockAIProvider(region=region, model_id=model_id)

    print("\nInvoking Amazon Bedrock Nova 2 Lite (Converse API)...")
    result: AIExtractionResult = await provider.extract_work_state(raw_notes)

    print("\nExtraction Succeeded! Validated against AIExtractionResult schema:")
    print("=" * 50)
    print(json.dumps(result.model_dump(), indent=2))
    print("=" * 50)

    print("\nSemantic Validation:")
    # 1. Completed work
    print(f"  [COMPLETED]    ({len(result.completed)} items):")
    for c in result.completed:
        print(f"    - {c.title}: {c.description}")

    # 2. Unresolved work
    print(f"  [UNRESOLVED]   ({len(result.unresolved)} items):")
    for u in result.unresolved:
        print(f"    - {u.title}: {u.description}")

    # 3. Commitments
    print(f"  [COMMITMENTS]  ({len(result.commitments)} items):")
    for com in result.commitments:
        print(f"    - {com.description} (To: {com.committed_to}, Date: {com.expected_date})")

    # 4. Blockers
    print(f"  [BLOCKERS]     ({len(result.blockers)} items):")
    for b in result.blockers:
        print(f"    - {b.description} (Blocked by: {b.blocked_by})")

    # 5. Deadlines
    print(f"  [DEADLINES]    ({len(result.deadlines)} items):")
    for d in result.deadlines:
        print(f"    - {d.description}: {d.date_str}")

    # 6. Exceptions
    print(f"  [EXCEPTIONS]   ({len(result.exceptions)} items):")
    for e in result.exceptions:
        print(f"    - Expected: {e.expected}")
        print(f"      Found:    {e.found}")
        print(f"      Evidence: {e.evidence}")
        print(f"      Action:   {e.required_action}")

    # 7. Next Actions
    print(f"  [NEXT ACTIONS] ({len(result.next_actions)} items):")
    for n in result.next_actions:
        print(f"    - {n.action} (Assignee: {n.assignee})")

    # Semantic assertions
    assert len(result.completed) > 0, "Expected at least one completed item (Payment API)"
    assert len(result.unresolved) > 0, "Expected at least one unresolved item (Webhook)"
    assert len(result.blockers) > 0, "Expected at least one blocker (Finance discount approval)"
    assert len(result.commitments) > 0 or len(result.deadlines) > 0, "Expected commitment or deadline (Friday)"
    assert len(result.next_actions) > 0, "Expected next actions"

    print("\n==================================================")
    print("SUCCESS: REAL BEDROCK NOVA 2 LITE EXTRACTION FULLY VERIFIED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(test_bedrock_extraction())
