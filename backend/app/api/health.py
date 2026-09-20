import os
from fastapi import APIRouter
from app.repositories import get_repository

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health():
    ai_provider = os.getenv("AI_PROVIDER", "mock")
    repo = get_repository()
    repo_health = repo.health_check()

    return {
        "status": "healthy",
        "service": "CONTINUITY Backend",
        "version": "1.0.0",
        "ai_provider": ai_provider,
        "repository": repo_health.get("provider", "memory"),
        "repository_status": repo_health.get("status", "healthy"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }
