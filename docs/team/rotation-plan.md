# Team Rotation Plan — Agent AI Bootcamp

**Goal:** Every team member touches agents, backend, frontend, AND infra by the end of camp.
**Assumption:** All 4 at equal skill level — no silos, no architects.

---

## Overview

| Phase | Epic | What you build | Owner |
|-------|------|---------------|-------|
| **Phase 1** | [Epic 5](../epics/epic-5-bootcamp-phase1-graph-skeleton.md) | LangGraph skeleton together (pair-program) | All 4 |
| **Phase 2** | [Epic 2](../epics/epic-2-agents.md) | Real agent nodes + cross-train layers | Each owns 2-3 PRs |
| **Phase 3** | [Epic 3](../epics/epic-3-deployment.md) | AWS infra deployment (infra rotation) | Each owns 1-2 |

---

## Phase 1 — Build the Graph Skeleton Together

All 4 on one machine, pair-programming. Everyone sees the LangGraph core built.

| Step | What you build | File |
|------|---------------|------|
| 1 | `GTMState` Pydantic model + field types | `agents/app/graph/state.py` |
| 2 | StateGraph with 5 nodes (orchestrator → research → strategy → content → brand_alignment) | `agents/app/graph/graph.py` |
| 3 | Conditional routing in orchestrator | `agents/app/graph/nodes/orchestrator.py` |
| 4 | Node stubs with simple echo output | All 5 node files |

**Done when:** `python -c "from agents.app.graph.graph import build_graph; print(build_graph())"` prints the compiled graph.

Epic file: [`docs/epics/epic-5-bootcamp-phase1-graph-skeleton.md`](../epics/epic-5-bootcamp-phase1-graph-skeleton.md)

---

## Phase 2 — Each Person Owns 1 Agent Node + Cross-Train Layer

| Person | Previous lane | Agent node | Non-agent layer | What they learn |
|--------|-------------|-----------|-----------------|----------------|
| **Nawaf** | Backend-only | Orchestrator (#9) + Content node (#12) | Content UI (#18) | LangGraph, LLM prompts, frontend |
| **Bader** | Frontend-only | Strategy node (#11) | Backend SSE (#14) | LangGraph agents, FastAPI streaming |
| **Abdulrahem** | ML/RAG | Research node (#10) + ColdIQ tools (#16) | — | LangChain tool wrappers |
| **Yousef** | Everything | Brand alignment (#13) + pm-skills (#15) | Strategy UI (#17) | pgvector RAG, frontend (delegates) |

**Swap rule:** After each PR is merged, rotate who reviews.
- Nawaf's PRs → Bader reviews
- Bader's PRs → Abdulrahem reviews
- Abdulrahem's PRs → Yousef reviews
- Yousef's PRs → Nawaf reviews

**Done when:** A full Research → Strategy → Content → Brand run produces output in the UI.

Epic file: [`docs/epics/epic-2-agents.md`](../epics/epic-2-agents.md)

---

## Phase 3 — Infra Rotation (Everyone Picks Something New)

| Person | Phase 2 role | Epic 3 assignment | What they learn |
|--------|-------------|-------------------|----------------|
| **Nawaf** | Agents + Frontend | CloudFront CDN (#23) | CDN, edge caching |
| **Bader** | Agents + Backend | OIDC + deploy pipeline (#20) | CI/CD, IAM roles |
| **Abdulrahem** | Agents + MCP tools | ECS cluster (#19) + MCP extras (#24) | AWS ECS Fargate, Terraform |
| **Yousef** | RAG + Frontend | RDS + ElastiCache (#21) + S3 (#22) | Managed DB, storage services |

**Done when:** `docker compose -f infra/docker-compose.yml up --build` passes and all health endpoints respond.

Epic file: [`docs/epics/epic-3-deployment.md`](../epics/epic-3-deployment.md)

---

## Why This Works

- **Phase 1** — shared foundation. Everyone knows the graph shape.
- **Phase 2** — each person owns meaningful agent nodes AND steps outside their comfort zone. No "frontend guy" or "backend guy."
- **Phase 3** — everyone pops the cloud cherry. No infra silo either.
- **Review rotation** — no single reviewer bottleneck. Everyone reads everyone's code.

## PR Flow

```
staging ← feature branch (epic-5/pr-N-<name>)
   ↑
Open PR → tag assigned reviewer (see rotation above)
   ↓
Merge → next person pulls staging and starts theirs
```

## Total PRs Per Person

| Person | Phase 1 | Phase 2 | Phase 3 | Total |
|--------|---------|---------|---------|-------|
| **Nawaf** | shared | 3 PRs (#9, #12, #18) | 1 PR (#23) | 4 PRs |
| **Bader** | shared | 2 PRs (#11, #14) | 1 PR (#20) | 3 PRs |
| **Abdulrahem** | shared | 2 PRs (#10, #16) | 2 PRs (#19, #24) | 4 PRs |
| **Yousef** | shared | 3 PRs (#13, #15, #17) | 2 PRs (#21, #22) | 5 PRs |
| **All 4 paired** | 1 PR (#0) | — | 1 PR (#25) | 2 PRs paired |

Within 1 PR of each other. Balanced.
