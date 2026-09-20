# CONTINUITY Frontend

Modern, high-reliability workplace operations interface built for the CONTINUITY platform.

## Tech Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React

## Screens Implemented

1. **Employee 1 — My Work (`/`)**: Active operational case overview owned by Arun Kumar, displaying deadlines, blockers, and the prominent `[Create Handoff]` CTA.
2. **Create Handoff (`/handoff/new`)**: Unstructured notes intake with metadata fields (outgoing/incoming employee, handoff date) and a 1-click sample filler for demoing.
3. **Handoff Processing (`/handoff/processing`)**: Multi-stage animated fact extraction checklist calling the FastAPI backend.
4. **Continuity Queue (`/queue`)**: Incoming shift control center for Priya Sharma with KPI counters (Unresolved, At Risk, Blocked, Exceptions) and actionable cards.
5. **Case Detail (`/cases/[id]`)**: Deep-dive case operational view with commitments, blockers, exceptions, next actions, and interactive action buttons (`[Mark Resolved]`, `[Reassign]`, `[Escalate]`).

## Running Locally

```bash
cd frontend
npm install
npm run dev
```

The application runs on `http://localhost:3000`.
Make sure the FastAPI backend is running on `http://localhost:8000`.
