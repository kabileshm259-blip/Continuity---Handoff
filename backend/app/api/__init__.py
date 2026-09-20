from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.queue import router as queue_router
from app.api.handoff import router as handoff_router
from app.api.cases import router as cases_router
from app.api.deadlines import router as deadlines_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(queue_router)
api_router.include_router(handoff_router)
api_router.include_router(cases_router)
api_router.include_router(deadlines_router)
