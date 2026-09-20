from fastapi import APIRouter
from app.services.deadline_service import DeadlineEvaluationService, DeadlineEvaluationSummary

router = APIRouter(tags=["Deadlines"])

@router.post("/deadlines/evaluate", response_model=DeadlineEvaluationSummary)
def trigger_deadline_evaluation():
    """Trigger an on-demand deadline evaluation across all cases.
    
    Evaluates deadlines against UTC time, updates case statuses idempotently,
    and records audit events for actual automated transitions.
    """
    service = DeadlineEvaluationService()
    return service.evaluate_all_cases()

@router.get("/deadlines/evaluate", response_model=DeadlineEvaluationSummary)
def check_deadline_evaluation():
    """Inspect or trigger deadline evaluation via GET for convenience."""
    service = DeadlineEvaluationService()
    return service.evaluate_all_cases()
