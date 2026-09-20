# CONTINUITY — Cloud Infrastructure Architecture

This document outlines the AWS target architecture and infrastructure setup for CONTINUITY.

## Architecture Overview

```
                      [ Client / Browser ]
                               │
                               ▼
                    [ Amazon CloudFront / Vercel ]
                               │
                               ▼
                   [ Amazon API Gateway (HTTP) ]
                               │
                               ▼
                     [ AWS Lambda (FastAPI) ]
                     ┌─────────┴─────────┐
                     ▼                   ▼
           [ Amazon Bedrock ]    [ Amazon DynamoDB ]
          (State Extraction)     (Single-Table Store)
                     │                   │
                     ▼                   ▼
              [ Amazon S3 ]    [ Amazon EventBridge ]
           (Evidence & Notes)   (Deadlines & Alerts)
```

---

## DynamoDB Table Setup (Phase 3)

The application uses Amazon DynamoDB as its durable persistence layer when `REPOSITORY_PROVIDER=dynamodb`.

### Table Specification
- **Table Name**: `continuity-cases-dev`
- **Region**: `ap-south-1` (or your configured `AWS_REGION`)
- **Partition Key**: `case_id` (String)
- **Billing Mode**: `PAY_PER_REQUEST` (On-Demand capacity)

### AWS CLI Command to Create Table

Run this command manually to create the table:

```bash
aws dynamodb create-table \
    --table-name continuity-cases-dev \
    --attribute-definitions AttributeName=case_id,AttributeType=S \
    --key-schema AttributeName=case_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-south-1
```

### Verify Table Creation

```bash
aws dynamodb describe-table \
    --table-name continuity-cases-dev \
    --region ap-south-1 \
    --query "Table.TableStatus"
```
The status should transition from `"CREATING"` to `"ACTIVE"`.

### Seeding DynamoDB with Demo Data

Once the table is active, populate the demo workplace cases:

```bash
cd backend
python scripts/seed_dynamodb.py
```

---

## Amazon S3 Evidence Storage Setup (Phase 4)

The application uses a private Amazon S3 bucket to store raw handoff notes and unedited operational evidence artifacts when `EVIDENCE_PROVIDER=s3`.

### Bucket Specification
- **Bucket Name**: `continuity-evidence-dev`
- **Region**: `ap-south-1` (or your configured `AWS_REGION`)
- **Access Policy**: Completely Private (Block Public Access enabled)
- **Object Key Structure**: `cases/{case_id}/evidence/{evidence_id}.txt`

### 1. AWS CLI Command to Create S3 Bucket

```bash
aws s3api create-bucket \
    --bucket continuity-evidence-dev \
    --region ap-south-1 \
    --create-bucket-configuration LocationConstraint=ap-south-1
```

### 2. Block All Public Access (Security Best Practice)

```bash
aws s3api put-public-access-block \
    --bucket continuity-evidence-dev \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 3. Verify Bucket Creation

```bash
aws s3api head-bucket --bucket continuity-evidence-dev --region ap-south-1
```
A return code of 0 (no output) indicates the bucket exists and is accessible.

### 4. Optional Bucket Cleanup (Delete When Tearing Down)

```bash
aws s3 rm s3://continuity-evidence-dev --recursive
aws s3api delete-bucket --bucket continuity-evidence-dev --region ap-south-1
```

---

## AWS Service Roles

### 1. Compute & API
- **AWS Lambda (Python 3.11)**: Runs the FastAPI backend serverless application packaged with Mangum or Lambda Web Adapter. Provides zero-idle cost and instant scaling.
- **Amazon API Gateway**: Manages HTTP endpoints, rate limiting, and CORS routing to the Lambda function.

### 2. AI Intelligence
- **Amazon Bedrock**:
  - Model: Anthropic Claude 3.5 Sonnet / Claude 3 Haiku or Amazon Nova.
  - Role: Strictly extracts structured facts (`completed`, `unresolved`, `commitments`, `blockers`, `deadlines`, `exceptions`, `next_actions`) from unstructured handoff notes.
  - Note: Bedrock does NOT make policy decisions or set operational statuses; that is handled by deterministic code in the policy engine.

### 3. Persistence
- **Amazon DynamoDB**:
  - Table: `continuity-cases-dev`
  - Partition Key: `case_id` (String)
  - Stores complete `Case` records with nested tasks, commitments, blockers, exceptions, evidence references, and audit history.
  - Stores `Handoff` records using partition key `case_id = "HANDOFF#<handoff_id>"`.

### 4. Storage
- **Amazon S3**:
  - Bucket: `continuity-evidence-dev`
  - Stores raw handoff note archives, photo attachments (e.g. damaged product evidence), and invoice PDF artifacts.
  - S3 object keys are referenced by `Case.evidence_records`.

## Amazon EventBridge Scheduled Deadlines (Phase 5 & 5B — DEPLOYED)

CONTINUITY integrates Amazon EventBridge to evaluate time-dependent workplace handoffs and commitments automatically.

### Architecture

```
[ Amazon EventBridge Scheduler ] (Rate: rate(1 hour))
              │
              ▼
    [ AWS Lambda Handler ] (continuity-deadline-evaluator)
              │
              ├──────────────────────────────────────────┐
              ▼                                          ▼
   [ Amazon DynamoDB ]                          [ Policy Engine ]
(Scan / query active cases)             (Deterministic UTC deadline check)
              │                                          │
              └──────────────────┬───────────────────────┘
                                 ▼
                       [ Amazon DynamoDB ]
             (Idempotent update + CASE_STATUS_CHANGED audit event)
```

### Deployed AWS Resources (ap-south-1)

| Resource | Name / ARN | Status |
|---|---|---|
| **AWS Lambda Function** | `continuity-deadline-evaluator`<br>`arn:aws:lambda:ap-south-1:336814727375:function:continuity-deadline-evaluator` | `ACTIVE` |
| **Lambda Execution Role** | `continuity-deadline-evaluator-role`<br>`arn:aws:iam::336814727375:role/continuity-deadline-evaluator-role` | `ACTIVE` |
| **EventBridge Schedule** | `continuity-deadline-evaluator-schedule`<br>`arn:aws:scheduler:ap-south-1:336814727375:schedule/default/continuity-deadline-evaluator-schedule` | `ENABLED` |
| **Scheduler Role** | `continuity-scheduler-role`<br>`arn:aws:iam::336814727375:role/continuity-scheduler-role` | `ACTIVE` |
| **DynamoDB Table** | `continuity-cases-dev`<br>`arn:aws:dynamodb:ap-south-1:336814727375:table/continuity-cases-dev` | `ACTIVE` |

### Key Principles

1. **Deterministic Execution**:
   - The AI extracts commitments, deadlines, and blockers from handoff text.
   - Code alone calculates whether a deadline is `OVERDUE` (elapsed in UTC) or `AT_RISK` (within 24h threshold with an active blocker).
2. **Strict Idempotency**:
   - Re-running the evaluation does not trigger duplicate state transitions or duplicate audit events for unchanged conditions.
3. **Auditable System Transitions**:
   - When a status transition occurs, an `AuditEvent` is recorded with `actor="SYSTEM"`, `action="CASE_STATUS_CHANGED"`, and details including the evaluated UTC timestamp and rationale.

### Verification Commands

#### 1. Invoke Lambda Manually via AWS CLI
```bash
aws lambda invoke \
    --function-name continuity-deadline-evaluator \
    --payload '{"source": "manual-test"}' \
    --cli-binary-format raw-in-base64-out \
    response.json \
    --region ap-south-1

cat response.json
```

#### 2. Check EventBridge Schedule Configuration
```bash
aws scheduler get-schedule \
    --name continuity-deadline-evaluator-schedule \
    --region ap-south-1
```

#### 3. Run Live End-to-End Test with Controlled Cases
```bash
cd backend
python scripts/live_lambda_test.py
```

---

## AWS Service Roles

### 1. Compute & API
- **AWS Lambda (Python 3.11)**: Runs the FastAPI backend serverless application packaged with Mangum or Lambda Web Adapter. Provides zero-idle cost and instant scaling.
- **Dedicated Lambda (`continuity-deadline-evaluator`)**: Standalone lightweight function triggered by EventBridge for periodic deadline enforcement.
- **Amazon API Gateway**: Manages HTTP endpoints, rate limiting, and CORS routing to the Lambda function.

### 2. AI Intelligence
- **Amazon Bedrock**:
  - Model: Anthropic Claude 3.5 Sonnet / Claude 3 Haiku or Amazon Nova.
  - Role: Strictly extracts structured facts (`completed`, `unresolved`, `commitments`, `blockers`, `deadlines`, `exceptions`, `next_actions`) from unstructured handoff notes.
  - Note: Bedrock does NOT make policy decisions or set operational statuses; that is handled by deterministic code in the policy engine.

### 3. Persistence
- **Amazon DynamoDB**:
  - Table: `continuity-cases-dev`
  - Partition Key: `case_id` (String)
  - Stores complete `Case` records with nested tasks, commitments, blockers, exceptions, evidence references, and audit history.
  - Stores `Handoff` records using partition key `case_id = "HANDOFF#<handoff_id>"`.

### 4. Storage
- **Amazon S3**:
  - Bucket: `continuity-evidence-dev`
  - Stores raw handoff note archives, photo attachments (e.g. damaged product evidence), and invoice PDF artifacts.
  - S3 object keys are referenced by `Case.evidence_records`.

### 5. Event-Driven Deadlines & Schedules
- **Amazon EventBridge**:
  - Schedule: `continuity-deadline-evaluator-schedule` (`rate(1 hour)`).
  - Triggers `continuity-deadline-evaluator` to transition cases to `OVERDUE` or `AT_RISK`.

## Phase Progression
- **Phase 1**: Local FastAPI + Next.js + In-Memory Thread-Safe Repository + Mock AI Provider.
- **Phase 2**: Amazon Bedrock abstraction and integration.
- **Phase 3**: Amazon DynamoDB repository implementation, safe seed script, and repository factory.
- **Phase 4**: Amazon S3 evidence storage implementation, predictable object key structure, and evidence audit logging.
- **Phase 5 & 5B (Completed)**: Real EventBridge schedule and Lambda function deployed to AWS (`ap-south-1`), deterministic policy evaluation, idempotency, and automated audit trails verified live.
