# ReachGTM

**AI-powered multi-agent Go-To-Market strategy platform.**  
Research → Strategy → Content. In minutes, not weeks.

---

## What is ReachGTM?

ReachGTM automates the GTM strategy pipeline that currently requires a marketing team, a sales consultant, and a copywriter working for days. You describe your company. Five AI agents — Research, Strategy, Content, Brand Alignment, and an Orchestrator — collaborate to produce a full GTM strategy: market research, ICP definition, value propositions, competitive battlecards, cold email sequences, and LinkedIn posts.

Unlike ChatGPT (one-shot prompts) or Jasper (template-based), ReachGTM uses a stateful multi-agent graph with persistent memory, RAG-based brand validation, and real-time streaming. Unlike HubSpot, it's a strategy tool, not a CRM.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), TanStack Query 5, Zustand 5, Tailwind CSS 4 |
| API | FastAPI 0.136 (Python 3.11) |
| Agents | LangGraph 1.2 (StateGraph + conditional routing) |
| LLM | OpenAI gpt-4o-mini |
| Embeddings | text-embedding-3-small (1536 dims) |
| Vector Store | pgvector on PostgreSQL 16 (HNSW, m=16) |
| Cache / Rate limit | Redis 7 (sliding window, 100 req/min per tenant) |
| MCP Tools | Perplexity (research), Databar, Fetch, Attio (Phase 2) |
| Observability | LangSmith Cloud |
| Deployment | AWS ECS Fargate + ECR (prod) / Docker Compose (local) |

---

## System Architecture

```
┌─────────────┐     HTTPS      ┌──────────────────┐    HTTP    ┌──────────────────┐
│  Browser    │ ─────────────► │  FastAPI Backend  │ ─────────► │  FastAPI Agents  │
│  Next.js 16 │ ◄── SSE ─────  │  :8000            │           │  LangGraph :8001  │
└─────────────┘                └──────────────────┘           └──────────────────┘
                                        │                               │
                                   asyncpg pool                    asyncpg pool
                                        │                               │
                               ┌─────────────────┐         ┌──────────────────────┐
                               │  PostgreSQL 16   │         │  Redis 7             │
                               │  + pgvector      │         │  (rate limit, cache) │
                               │  HNSW index      │         └──────────────────────┘
                               └─────────────────┘
```

---

## Agent Architecture

```
START
  ↓
[orchestrator] ── routes based on state ──────────────────────┐
  ↓ (no research)                                             │ (strategy exists)
[research] → Perplexity MCP → ResearchReport                  │
  ↓                                                           │
[strategy] → GTMStrategy (ICP, channels, battlecards)         │
  ↓ ◄─────────────────────────────────────────────────────────┘
[content] → ContentAsset[] (cold emails, LinkedIn posts)
  ↓
[brand_alignment] → RAG retrieval → score → revise (max 2x) → validated assets
  ↓
END
```

---

## Domain Model

| Table | Description |
|---|---|
| `companies` | One row per tenant. `plan` = free/pro/enterprise |
| `users` | Multi-seat team members with `role` = owner/admin/member |
| `sessions` | Refresh token store (30-day expiry) |
| `knowledge_documents` | Uploaded PDF/DOCX metadata |
| `document_chunks` | 512-word chunks with 1536-dim pgvector embedding |
| `strategies` | Generated GTMStrategy JSON (one per session) |
| `content_assets` | Generated cold emails, LinkedIn posts, etc. |
| `company_memory` | Persistent key-value context across sessions |

Row-Level Security enforced on all tenant tables via `SET LOCAL app.current_company_id`.

---

## Key Flows

**1. Register & onboard**
```
POST /auth/register → JWT tokens → redirect to /knowledge → upload brand guide → indexed in pgvector
```

**2. Generate GTM strategy**
```
POST /strategy/generate → SSE stream → 5 agents run → ResearchReport + GTMStrategy + ContentAsset[] → persisted to DB
```

**3. Brand-aligned content**
```
content_node generates draft → brand_alignment_node retrieves brand chunks → scores 0-1 → revises if <0.7 → approved
```

---

## Project Structure

```
ReachGTM/
├── shared/schemas.py          # Single source of truth — all Pydantic models
├── agents/                    # LangGraph agent service (port 8001)
│   ├── app/graph/             # StateGraph, 5 nodes, conditional routing
│   ├── app/prompts/           # System prompts per agent
│   └── app/tools/             # PgVectorRetriever, MCP client, skills
├── backend/                   # FastAPI backend (port 8000)
│   ├── app/api/               # auth, strategy, content, knowledge, chat routers
│   ├── app/middleware/        # TenantMiddleware (JWT→company_id), RateLimitMiddleware
│   ├── app/db/                # asyncpg pool, init.sql (tables + RLS + HNSW)
│   └── app/services/          # auth_service, knowledge_service, storage_service
├── frontend/                  # Next.js 16 App Router (port 3000)
│   ├── app/                   # Pages (auth, dashboard, strategy, content, knowledge)
│   ├── components/agent/      # AgentProgress (real), AgentEventFeed (stub)
│   ├── hooks/                 # useAgentStream (SSE), useAuth
│   └── lib/                   # axios API client, auth helpers, cn utility
├── infra/
│   ├── docker-compose.yml     # 5 services with healthchecks
│   └── docker-compose.prod.yml # ECS resource limits + CloudWatch logging
├── docs/                      # Architecture, API, agents, deployment, epics
├── .github/workflows/         # ci.yml (lint+test), deploy.yml (ECR+ECS+OIDC)
└── CLAUDE.md                  # AI agent context file
```

---

## Environments

| Environment | URL | Deploy trigger |
|---|---|---|
| Local | http://localhost:3000 | `docker compose up --build` |
| Staging | Auto-deploy on merge to `staging` | CI/CD |
| Production | Merge `staging` → `main` | `deploy.yml` |

---

## Local Setup

```bash
git clone https://github.com/yousef4git/ReachGTM.git
cd ReachGTM
cp .env.example .env
# Required: OPENAI_API_KEY, JWT_SECRET (any 32-char random string)
docker compose -f infra/docker-compose.yml up --build
```

Verify:
```bash
curl http://localhost:8000/health   # {"service":"backend","status":"ok"}
curl http://localhost:8001/health   # {"service":"agents","status":"ok"}
```

---

## Roles & Permissions

| Role | Register | Invite | Generate strategy | Upload knowledge | Admin |
|---|---|---|---|---|---|
| owner | ✓ | ✓ | ✓ | ✓ | ✓ |
| admin | — | ✓ | ✓ | ✓ | — |
| member | — | — | ✓ | ✓ | — |

All DB queries are filtered by `company_id` via PostgreSQL RLS — no application-level tenant checks needed.

---

## Multi-Tenancy

Shared-schema PostgreSQL with Row-Level Security. Each request sets `SET LOCAL app.current_company_id = '{uuid}'` via the asyncpg pool, which activates the RLS policy on every tenant table. The `postgres` superuser role bypasses RLS for migrations.

---

## MCP Tools

| Tool | Provider | Used by | Available |
|---|---|---|---|
| `perplexity.search` | Perplexity AI | Research agent | Epic 1 |
| `databar.enrich` | Databar | Research agent | Epic 3 |
| `fetch.url` | Fetch MCP | Research agent | Epic 3 |
| `attio.contacts` | Attio | Strategy agent | Phase 2 |

---

## Roadmap

- [x] **Phase 1 (MVP)** — LangGraph agents, FastAPI, Next.js, pgvector, Docker, AWS ECS
- [ ] **Phase 2** — Multi-seat teams, real-time collaboration, CRM connectors (HubSpot, Attio)
- [ ] **Phase 3** — Analytics dashboard, A/B content variants, multi-region, SOC 2

---

## Epics & PR Plan

| Epic | Focus | PRs | Status |
|---|---|---|---|
| Epic 1 | Foundation scaffold | #1–#8 | In progress |
| Epic 2 | Real agent implementations + SSE | #9–#18 | Planned |
| Epic 3 | AWS production deployment | #19–#25 | Planned |
| Epic 4 | Phase 2 features | Issues | Backlog |

See `docs/epics/` for full PR breakdowns and acceptance criteria.

---

## Team

| Name | Role | Area |
|---|---|---|
| Yousef | Architecture lead | LangGraph, orchestration, infra |
| Nawaf | Backend engineer | FastAPI, PostgreSQL, auth |
| Bader | Frontend engineer | Next.js, SSE streaming UI |
| Abdulrahem | ML engineer | RAG pipeline, pgvector, MCP tools |

---

## License

MIT © 2026 ReachGTM
