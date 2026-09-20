import asyncio
import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
load_dotenv()

from app.models.case import HandoffRequest
from app.services.handoff_service import HandoffService

async def run_e2e():
    print("=== END-TO-END HANDOFF TEST WITH BEDROCK NOVA 2 LITE ===")
    service = HandoffService()
    print(f"AI Provider:       {type(service.ai_provider).__name__} (Model: {getattr(service.ai_provider, 'model_id', None)})")
    print(f"Repository:        {type(service.repo).__name__}")
    print(f"Evidence Service:  {type(service.evidence_service).__name__}")
    
    req = HandoffRequest(
        outgoing_employee="Arun Kumar",
        incoming_employee="Priya Sharma",
        raw_notes="Payment API integration is complete. Webhook handling is still pending. Finance has not approved the discount yet. I promised the client the revised version before Friday. Follow up with Finance and finish webhook validation."
    )
    
    print("\nProcessing handoff through HandoffService...")
    resp = await service.process_handoff(req)
    print(f"Handoff ID:        {resp.handoff_id}")
    print(f"Cases Created:     {resp.cases_created}")
    print(f"Cases Updated:     {resp.cases_updated}")
    print(f"Extraction Summary:\n{json.dumps(resp.extraction_summary, indent=2)}")
    
    # Verify in DynamoDB and S3
    if resp.cases_created:
        new_case_id = resp.cases_created[0]
        saved_case = service.repo.get_case(new_case_id)
        print(f"\nDynamoDB Verified Case: {saved_case.case_id}")
        print(f"  Title:        {saved_case.title}")
        print(f"  Status:       {saved_case.status.value} (Deterministic Policy Engine output)")
        print(f"  Priority:     {saved_case.priority.value}")
        print(f"  Owner:        {saved_case.owner}")
        print(f"  Deadline:     {saved_case.deadline}")
        print(f"  Blockers:     {len(saved_case.blockers)}")
        print(f"  Next Action:  {saved_case.next_action}")
        print(f"  Audit Events: {len(saved_case.audit_history)}")
        for evt in saved_case.audit_history:
            print(f"    - [{evt.actor}] {evt.action}: {evt.details}")
            
        print(f"  Evidence Records: {len(saved_case.evidence_records)}")
        for ev in saved_case.evidence_records:
            print(f"    - S3 Key: {ev.object_key}, Size: {ev.size_bytes} bytes")
            # Verify S3 retrieval
            content_bytes, meta = service.evidence_service.get_evidence(ev.object_key)
            print(f"    - S3 Retrieved Content: {content_bytes.decode('utf-8')[:80]}...")
            
    print("\n=== E2E TEST COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(run_e2e())
