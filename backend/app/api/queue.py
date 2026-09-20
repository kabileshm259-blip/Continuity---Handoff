from typing import Optional
from fastapi import APIRouter, Query
from app.models.case import QueueResponse
from app.services.case_service import CaseService

router = APIRouter(tags=["Queue"])

@router.get("/queue", response_model=QueueResponse)
def get_continuity_queue(owner: Optional[str] = Query(None, description="Optional owner filter")):
    service = CaseService()
    return service.get_queue(owner_filter=owner)
