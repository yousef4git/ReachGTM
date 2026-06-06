# ReachGTM — Deployment Guide

## Prerequisites

- Docker Desktop 4.x+
- Node.js 20+
- Python 3.11+
- AWS CLI v2 (production only)
- `gh` CLI (for PR workflow)

---

## Local Development

```bash
# 1. Clone and enter repo
git clone https://github.com/yousef4git/ReachGTM.git
cd ReachGTM

# 2. Copy and fill environment
cp .env.example .env
# Required: OPENAI_API_KEY, JWT_SECRET (any random 32-char string)
# Optional: LANGSMITH_API_KEY, PERPLEXITY_API_KEY

# 3. Start all services
docker compose -f infra/docker-compose.yml up --build

# 4. Verify health
curl http://localhost:8000/health   # {"service":"backend","status":"ok"}
curl http://localhost:8001/health   # {"service":"agents","status":"ok"}
curl http://localhost:3000          # HTML

# 5. Verify DB
docker compose -f infra/docker-compose.yml exec db psql -U postgres -d reachgtm -c "\dt"
# Should show: companies, users, sessions, knowledge_documents, document_chunks,
#              strategies, content_assets, company_memory
```

### Restart a single service
```bash
docker compose -f infra/docker-compose.yml restart backend
```

### View logs
```bash
docker compose -f infra/docker-compose.yml logs -f agents
```

---

## Running Tests Locally

```bash
# Backend tests (requires local Python env)
pip install -r backend/requirements.txt
JWT_SECRET=test OPENAI_API_KEY=test DATABASE_URL=postgresql://postgres:password@localhost:5432/reachgtm REDIS_URL=redis://localhost:6379 pytest backend/tests/ -v

# Agent tests
pip install -r agents/requirements.txt
OPENAI_API_KEY=test DATABASE_URL=postgresql://postgres:password@localhost:5432/reachgtm REDIS_URL=redis://localhost:6379 pytest agents/tests/ -v

# Or via Docker
docker compose -f infra/docker-compose.yml run --rm backend pytest backend/tests/ -v
docker compose -f infra/docker-compose.yml run --rm agents pytest agents/tests/ -v
```

---

## Staging Environment

Staging auto-deploys when a PR merges to the `staging` branch via GitHub Actions CI.

The deploy workflow (`deploy.yml`) triggers only on push to `main`. For staging, configure a separate workflow or environment in GitHub Actions that targets your staging ECS cluster.

### View staging logs
```bash
aws ecs describe-tasks --cluster reachgtm-staging --tasks <task-arn>
aws logs get-log-events --log-group /ecs/reachgtm-backend --log-stream-name ecs/backend/<task-id>
```

---

## Production Deployment

Production deploys automatically when staging is merged to `main` via the deploy workflow.

### First-time AWS setup

1. **Create ECR repositories:**
```bash
aws ecr create-repository --repository-name reachgtm-backend
aws ecr create-repository --repository-name reachgtm-agents
aws ecr create-repository --repository-name reachgtm-frontend
```

2. **Create OIDC provider for GitHub Actions:**
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com
```

3. **Create IAM role `reachgtm-deploy` with trust policy for GitHub OIDC and permissions for ECR push + ECS update-service.**

4. **Store role ARN in GitHub Secrets as `AWS_DEPLOY_ROLE_ARN`.**

5. **Create ECS cluster and services:**
```bash
aws ecs create-cluster --cluster-name reachgtm-prod
# Then create task definitions and services for backend, agents, frontend
```

### Rollback
```bash
# Redeploy previous task definition
aws ecs update-service \
  --cluster reachgtm-prod \
  --service reachgtm-backend \
  --task-definition reachgtm-backend:<previous-revision>
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `JWT_SECRET` | Yes | — | Random 32+ char string |
| `DATABASE_URL` | Yes | — | asyncpg-compatible PostgreSQL URL |
| `REDIS_URL` | Yes | — | Redis connection URL |
| `LANGSMITH_API_KEY` | No | `""` | LangSmith observability |
| `PERPLEXITY_API_KEY` | No | `""` | Research agent MCP tool |
| `AGENTS_URL` | No | `http://agents:8001` | Internal agents service URL |
| `ENVIRONMENT` | No | `development` | `development` or `production` |
