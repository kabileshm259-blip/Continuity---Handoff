import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load local environment if present
load_dotenv()

from app.api import api_router

app = FastAPI(
    title="CONTINUITY — Workplace Handoff Intelligence API",
    description="Operational handoff engine: AI extracts facts, deterministic code decides and enforces.",
    version="1.0.0"
)

# CORS configuration for local development and frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {
        "product": "CONTINUITY — Workplace Handoff Intelligence",
        "docs": "/docs",
        "health": "/health",
        "queue": "/queue"
    }
