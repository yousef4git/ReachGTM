# ReachGTM — Claude Code Context

## Project Overview
ReachGTM is an AI-powered multi-agent Go-To-Market strategy platform. It automates the Research → Strategy → Content pipeline that normally takes marketing teams days. A 4-person AI-assisted team is building the MVP in 3 weeks using LangGraph, FastAPI, Next.js, PostgreSQL+pgvector, and Redis.

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), TanStack Query 5, Zustand 5, Tailwind CSS 4, shadcn/ui |
| API | FastAPI 0.136 (Python 3.11) |
| Agents | LangGraph 1.2 (StateGraph) |
| LLM | OpenAI (gpt-4o-mini) |
| Embeddings | text-embedding-3-small (1536 dims) |
| Vector Store | pgvector on PostgreSQL 16 (HNSW index) |
| Cache | Redis 7 |
| MCP Tools | Perplexity, Databar, Fetch, Attio (Phase 2) |
| Observability | LangSmith Cloud |
| Deployment | AWS ECS Fargate, ECR, RDS, ElastiCache, S3, CloudFront |

## Team & Ownership
| Name | Area |
|---|---|
| Yousef | Architecture lead — LangGraph, orchestration, infra |
| Nawaf | FastAPI backend, PostgreSQL, auth |
| Bader | Next.js frontend, SSE streaming UI |
| Abdulrahem | RAG pipeline, pgvector, MCP tool integrations |

## Branch Strategy
- `staging` is the **default branch** — all PRs target staging
- `main` is **protected** — merged from staging only, triggers prod deploy
- Feature branches: `epic-N/pr-N-<name>`
- **Never commit directly to staging or main**

## Startup (local dev)
```bash
cp .env.example .env
# Fill in OPENAI_API_KEY, JWT_SECRET, LANGSMITH_API_KEY, PERPLEXITY_API_KEY
docker compose -f infra/docker-compose.yml up --build
```

Health check URLs:
- Backend: http://localhost:8000/health
- Agents: http://localhost:8001/health
- Frontend: http://localhost:3000
- DB: `psql postgresql://postgres:password@localhost:5432/reachgtm`

## Shared Schemas Contract
`shared/schemas.py` is the **single source of truth** for all data models. Rules:
1. Changes to `shared/schemas.py` require a PR reviewed by ALL four team members
2. When you change a Pydantic model, update `frontend/types/index.ts` in the same PR
3. Never import from `shared/` using relative paths — always `from shared.schemas import ...`

## Sub-Agent Development Workflow
When implementing an Epic PR:
1. Create branch: `git checkout -b epic-N/pr-N-<name>`
2. Invoke `superpowers:subagent-driven-development` for the relevant plan tasks
3. Each task = one commit (see plan tasks)
4. Run `docker compose up --build` and verify health endpoints before opening PR
5. PR targets `staging`, not `main`
6. Tag the relevant team member as reviewer per CODEOWNERS

## Current Epic
**Epic 1 — Foundation** (Week 1)
See `docs/epics/epic-1-foundation.md` for all 8 PRs and acceptance criteria.

## Version Policy
**Never hardcode package versions.** Use context7 to resolve latest stable before any `requirements.txt` or `package.json` change.

## Docs Index
- `docs/architecture.md` — Why LangGraph, why pgvector, why RLS, why ECS Fargate
- `docs/api.md` — Complete API reference (every endpoint, request/response types)
- `docs/agents.md` — Agent reference (inputs, outputs, prompts, MCP tools, LangSmith tags)
- `docs/deployment.md` — Local, staging, and production deployment guide
- `docs/test-plan.md` — Project-wide test strategy, coverage gates, per-PR checklist
- `docs/epics/` — Epic-by-Epic PR plan with acceptance criteria
