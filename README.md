# CONTINUITY — Workplace Handoff Intelligence

> "CONTINUITY makes sure work doesn't get lost when it moves from one employee to another."

## The Problem

In modern workplaces, work is continuously handed from Employee 1 to Employee 2. While the task assignment is transferred, the critical operational context is lost across scattered channels:
- WhatsApp & Slack/Teams messages
- Emails and forwarded threads
- PDFs, spreadsheets, and personal notes
- Ticket comments and verbal hallways chats

When Employee 2 takes over, they are left deciphering:
- What has already been completed?
- What is still unresolved?
- What was promised to the customer/stakeholder and by when?
- Who is responsible or blocking progress?
- What is urgent, approaching deadline, or in conflict?
- What is the immediate next action?

## The Solution

**CONTINUITY** turns messy handoff information into structured, accountable work. 

Instead of letting AI hallucinate or make operational decisions, CONTINUITY enforces a clean architectural separation:
1. **AI extracts and explains** — parses unstructured text into structured factual items (commitments, blockers, deadlines, exceptions).
2. **Deterministic code decides and enforces** — a policy engine evaluates facts against business rules to establish operational status (`UNRESOLVED`, `AT_RISK`, `BLOCKED`, `EXCEPTION`, `OVERDUE`, `RESOLVED`).

## Core Workflow

```
Employee 1 (Arun Kumar)
       │
       ▼
Messy Work Notes / Handoff Information
       │
       ▼
CONTINUITY Platform
       │
       ▼
AI Extracts Work State (Structured Facts)
       │
       ▼
Deterministic Policy Logic Evaluates It
       │
       ▼
Structured Handoff
       │
       ▼
Employee 2 (Priya Sharma)
       │
       ▼
Continuity Queue
       │
       ▼
Resolve / Reassign / Escalate Actions
       │
       ▼
Immutable Audit History
```

## Tech Stack

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, Lucide Icons
- **Backend**: Python 3.11, FastAPI, Pydantic v2, Uvicorn
- **AI Layer**: Amazon Bedrock abstraction with configurable `MockAIProvider` (for local development) and `BedrockAIProvider`
- **Database Target**: Amazon DynamoDB (in-memory repository for Phase 1 MVP)
- **Storage Target**: Amazon S3
- **Events & Deadlines**: Amazon EventBridge

## Local Setup

### Prerequisites
- Node.js 18+ (Node 24+ supported)
- Python 3.10+ (Python 3.11 recommended)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend will start at `http://localhost:8000`.
- Health check: `http://localhost:8000/health`
- Interactive API Docs: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:3000`.

## Environment Variables

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

| Variable | Description | Default / Example |
|---|---|---|
| `AI_PROVIDER` | AI provider implementation | `mock` (or `bedrock`) |
| `AWS_REGION` | AWS Region for Bedrock/DynamoDB | `us-east-1` |
| `BEDROCK_MODEL_ID` | Model identifier in Bedrock | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `NEXT_PUBLIC_API_URL` | Backend URL for Next.js client | `http://localhost:8000` |

## Current MVP Scope (Phase 1)

The current MVP focuses on the end-to-end user experience without requiring external AWS credentials:
- **Employee 1 — My Work**: View active operational workload.
- **Create Handoff**: Ingest unstructured notes with preloaded sample data.
- **Processing Stage**: Multi-step animated fact extraction.
- **Employee 2 — Continuity Queue**: Operational control center with KPI counters, categorized work cards, and next actions.
- **Case Detail View**: In-depth case context, commitments, blockers, exceptions, and live action triggers (`[Mark Resolved]`, `[Reassign]`, `[Escalate]`).
- **Audit History**: Complete event timeline tracking every modification.
