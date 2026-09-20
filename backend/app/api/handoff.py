from fastapi import APIRouter, HTTPException
from app.models.case import HandoffRequest, HandoffResponse
from app.services.handoff_service import HandoffService
from app.ai.exceptions import (
    BedrockConfigurationError,
    BedrockInferenceError,
    BedrockExtractionError
)

router = APIRouter(tags=["Handoff"])

@router.post("/handoff", response_model=HandoffResponse)
async def process_handoff(request: HandoffRequest):
    service = HandoffService()
    try:
        return await service.process_handoff(request)
    except BedrockConfigurationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (BedrockInferenceError, BedrockExtractionError) as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoff processing failed: {str(e)}")
