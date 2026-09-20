# CONTINUITY Backend API

FastAPI backend providing workplace handoff intelligence, state extraction, deterministic policy evaluation, and audit logging.

## Features
- **Deterministic Policy Engine**: Decides operational case statuses based on strict logic rather than probabilistic AI output.
- **AI Extraction Layer**: Configurable interface supporting both `MockAIProvider` and `BedrockAIProvider`.
- **In-Memory Repository**: Pre-seeded thread-safe state store for fast local development and testing.
- **Audit Logging**: Immutable chronological records of all case events, transitions, and reassignments.

## Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and active AI provider |
| `GET` | `/queue` | Continuity queue summary counts and active cases |
| `POST` | `/handoff` | Ingest messy handoff notes, extract facts, evaluate policy, and generate/update cases |
| `GET` | `/cases/{case_id}` | Retrieve complete case details, tasks, commitments, blockers, exceptions, and audit history |
| `POST` | `/cases` | Manually register a new case |
| `POST` | `/cases/{case_id}/action` | Perform operational action (`resolve`, `reassign`, `escalate`) |

## Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
