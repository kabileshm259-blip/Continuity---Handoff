from typing import List
from fastapi import APIRouter, Path
from app.models.case import Case, ActionRequest
from app.services.case_service import CaseService
from app.storage.repository import get_repository

router = APIRouter(tags=["Cases"])

@router.get("/cases", response_model=List[Case])
def list_cases():
    service = CaseService()
    return service.get_all_cases()

@router.post("/cases", response_model=Case)
def create_case(case: Case):
    repo = get_repository()
    return repo.save_case(case)

@router.get("/cases/{case_id}", response_model=Case)
def get_case(case_id: str = Path(..., description="Unique case identifier")):
    service = CaseService()
    return service.get_case(case_id)

@router.post("/cases/{case_id}/action", response_model=Case)
def perform_case_action(
    case_id: str = Path(..., description="Unique case identifier"),
    request: ActionRequest = ...
):
    service = CaseService()
    return service.execute_action(case_id, request)
