# Nawaf — Backend Engineer Guide

**Your role:** FastAPI backend, PostgreSQL, auth, S3 storage, RDS/ElastiCache provisioning.

---

## Your PRs

| Epic | PR | Branch | Title |
|---|---|---|---|
| 2 | #14 | `epic-2/pr-14-sse` | Backend SSE endpoint — `/strategy/generate/stream` |
| 3 | #21 | `epic-3/pr-21-rds` | RDS + ElastiCache provisioning |
| 3 | #22 | `epic-3/pr-22-s3` | S3 storage service (document uploads) |

---

## Local Setup

```bash
git clone https://github.com/yousef4git/ReachGTM.git
cd ReachGTM
cp .env.example .env
# Fill in: OPENAI_API_KEY, JWT_SECRET (any 32-char random string)
docker compose -f infra/docker-compose.yml up --build
```

Verify everything is running:
```bash
curl http://localhost:8000/health  # {"service":"backend","status":"ok"}
curl http://localhost:8001/health  # {"service":"agents","status":"ok"}
```

---

## PR #14 — Backend SSE Endpoint

**Branch:** `epic-2/pr-14-sse` (create from `staging`)

```bash
git checkout staging && git pull
git checkout -b epic-2/pr-14-sse
```

### What to build

Replace the stub in `backend/app/api/strategy.py` with a real SSE streaming endpoint that:
1. Receives `POST /api/v1/strategy/generate` with a `StrategyGenerateRequest` body
2. Persists a `strategies` row (status = `generating`)
3. Calls the agents service at `http://agents:8001/run` (pass `session_id`, `company_id`, `user_id`, `company_profile`)
4. Streams back SSE events from the agents service to the browser

### Files to modify

| File | Change |
|---|---|
| `backend/app/api/strategy.py` | Replace stub — real SSE streaming endpoint |
| `backend/app/services/strategy_service.py` | **Create new** — DB operations (insert strategy, update status, fetch by id) |
| `backend/app/api/strategy.py` | Add `GET /strategy/generate/stream` SSE route |

### SSE pattern to implement

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import asyncio, httpx, json
from backend.app.db.connection import get_db
from shared.schemas import StrategyGenerateRequest, AgentEvent

router = APIRouter(prefix="/strategy", tags=["strategy"])

@router.post("/generate")
async def generate_strategy(
    body: StrategyGenerateRequest,
    request: Request,
    conn = Depends(get_db),
):
    import uuid
    session_id = str(uuid.uuid4())
    company_id = request.state.company_id
    user_id = request.state.user_id

    # 1. Insert strategy row
    await conn.execute(
        "INSERT INTO strategies (session_id, company_id, user_id, status) VALUES ($1::uuid, $2::uuid, $3::uuid, 'generating')",
        session_id, company_id, user_id,
    )

    async def event_stream():
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST", "http://agents:8001/run",
                json={
                    "session_id": session_id,
                    "company_id": company_id,
                    "user_id": user_id,
                    "company_profile": body.company_profile.model_dump(),
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        yield f"data: {line}\n\n"
        yield "data: {\"event\":\"done\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@router.get("/{strategy_id}")
async def get_strategy(strategy_id: str, conn = Depends(get_db)):
    row = await conn.fetchrow("SELECT * FROM strategies WHERE id = $1::uuid", strategy_id)
    if not row:
        from fastapi import HTTPException
        raise HTTPException(404, "Strategy not found")
    return dict(row)
```

### Agents service `/run` endpoint (also your job to wire up)

The agents service stub in `agents/app/main.py` has a `/run` endpoint that returns `not_implemented`. You need to coordinate with **Yousef** — once he finishes PR #9 (orchestrator), wire the `/run` endpoint to invoke the compiled graph:

```python
# agents/app/main.py — update /run after Yousef merges PR #9
from agents.app.graph.graph import graph
from agents.app.graph.state import GTMState
import uuid

@app.post("/run")
async def run(body: dict):
    state = GTMState(
        session_id=uuid.UUID(body["session_id"]),
        company_id=uuid.UUID(body["company_id"]),
        user_id=uuid.UUID(body["user_id"]),
    )
    result = await graph.ainvoke(state.model_dump())
    return result
```

For SSE streaming from the graph, use LangGraph's `astream_events`.

### Test

```bash
# Register first to get a token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123","company_name":"Acme"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Test SSE stream
curl -N -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST http://localhost:8000/api/v1/strategy/generate \
  -d '{"company_profile":{"name":"Acme","industry":"SaaS","stage":"seed","description":"AI sales tool"}}'
# Should stream SSE events, ending with data: {"event":"done"}
```

### PR checklist

- [ ] SSE events arrive at curl in real time (not buffered)
- [ ] Strategy row inserted with `generating` status
- [ ] Status updates to `complete` after agents finish
- [ ] `pytest backend/tests/ -v` all pass
- [ ] PR targets `staging`, reviewer: @yousefalshuwayi

---

## PR #21 — RDS + ElastiCache Provisioning

**Branch:** `epic-3/pr-21-rds` (create from `staging` after Epic 2 merges)

### What to build

AWS infrastructure for managed PostgreSQL and Redis. Two options: Terraform (preferred) or CloudFormation.

**Files to create:**
- `infra/terraform/rds.tf` — RDS PostgreSQL 16 with pgvector extension
- `infra/terraform/elasticache.tf` — Redis 7 cluster
- `infra/terraform/variables.tf` — VPC, subnet, security group variables
- `infra/terraform/outputs.tf` — connection string outputs for ECS task env vars

### Key requirements

```hcl
# rds.tf — key settings
resource "aws_db_instance" "reachgtm" {
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t3.medium"
  allocated_storage    = 20
  storage_encrypted    = true
  multi_az             = false  # flip to true for production
  db_name              = "reachgtm"
  username             = "postgres"
  password             = var.db_password  # store in AWS Secrets Manager
  # Must be in same VPC as ECS tasks
  db_subnet_group_name = aws_db_subnet_group.reachgtm.name
  # RDS PostgreSQL supports pgvector — install via init.sql after provisioning
}
```

After RDS is up, run `backend/app/db/migrations/init.sql` to create tables, RLS policies, and the HNSW index.

### PR checklist

- [ ] `terraform plan` completes without errors
- [ ] RDS reachable from ECS task security group
- [ ] ElastiCache Redis reachable from ECS task security group
- [ ] pgvector extension installed (`CREATE EXTENSION vector`)
- [ ] init.sql executed (8 tables exist)
- [ ] Connection strings stored in AWS Secrets Manager, not in code

---

## PR #22 — S3 Storage Service

**Branch:** `epic-3/pr-22-s3` (create from `staging`)

### What to build

Replace the stub in `backend/app/services/storage_service.py` with real S3 upload/download using boto3.

```python
# backend/app/services/storage_service.py
import boto3
from botocore.exceptions import ClientError
from backend.app.config import settings

_s3 = None

def get_s3():
    global _s3
    if not _s3:
        _s3 = boto3.client("s3", region_name=settings.aws_region)
    return _s3

async def upload_to_s3(content: bytes, key: str) -> str:
    """Upload bytes to S3, return the object URL."""
    get_s3().put_object(
        Bucket=settings.s3_bucket_name,
        Key=key,
        Body=content,
    )
    return f"s3://{settings.s3_bucket_name}/{key}"

async def download_from_s3(key: str) -> bytes:
    response = get_s3().get_object(Bucket=settings.s3_bucket_name, Key=key)
    return response["Body"].read()

def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
    return get_s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket_name, "Key": key},
        ExpiresIn=expires_in,
    )
```

Update `backend/app/api/knowledge.py` to call `upload_to_s3` before inserting the document into the DB. Store the `s3_key` in `knowledge_documents.s3_key`.

### PR checklist

- [ ] File upload to S3 works in local dev (use MinIO in docker-compose for local S3)
- [ ] `s3_key` populated in `knowledge_documents` table after upload
- [ ] Presigned URL returned in upload response
- [ ] No AWS credentials hardcoded — uses IAM role in prod, `AWS_ACCESS_KEY_ID` env var locally

---

## Branch Rules (important)

```
main (protected — never push here directly)
  ↑ PR from staging only
staging (default — all your PRs go here)
  ↑ PR from your feature branch
epic-2/pr-14-sse  ← your branch
```

**Every PR:**
1. `git checkout staging && git pull`
2. `git checkout -b epic-N/pr-N-<name>`
3. Implement → commit → push
4. `gh pr create --base staging`
5. Tag @yousefalshuwayi as reviewer

---

## Questions

Ping Yousef on the graph's SSE streaming API before starting PR #14 — the agents `/run` endpoint shape determines your SSE proxy pattern.
