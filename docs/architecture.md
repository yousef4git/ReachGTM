# ReachGTM — Architecture Decisions

## System Overview

ReachGTM is a multi-service platform: a Next.js frontend talks to a FastAPI backend, which dispatches work to a separate FastAPI-wrapped LangGraph agent service. All services share a PostgreSQL database (with pgvector extension) and a Redis cache.

```
Browser → Next.js (3000) → FastAPI Backend (8000) → FastAPI Agents (8001)
                                     ↓                      ↓
                              PostgreSQL + pgvector     Redis
                              (companies, users, 
                               strategies, chunks)
```

---

## Decision 1: LangGraph over OpenAI Agents SDK

**Score: LangGraph 9/10 vs OpenAI Agents SDK 6/10** (from PRD evaluation matrix)

LangGraph was chosen for three reasons that matter at our scale:

1. **Native PostgreSQL checkpointing** — `langgraph-checkpoint-postgres` persists graph state after every node. If the agents service restarts mid-run, it resumes from the last checkpoint. OpenAI Agents SDK has no built-in persistence.
2. **Conditional edge routing** — `add_conditional_edges("orchestrator", _route_fn)` lets us skip Research + Strategy and jump straight to Content if a strategy already exists. This is expressed as a graph topology, not control flow inside a node.
3. **Intermediate state streaming** — LangGraph emits state snapshots after each node. We use these to push SSE events (`AGENT_START`, `AGENT_COMPLETE`) without polling.

---

## Decision 2: pgvector over Pinecone or Weaviate

Keeping vectors in PostgreSQL reduces the operational surface from 4 services to 3.

1. **No extra infra** — pgvector is an extension on the existing PostgreSQL 16 instance. No vector DB to provision, monitor, or pay for separately.
2. **HNSW index performance** — With `m=16, ef_construction=64`, pgvector handles 1M+ vectors with sub-10ms p99 at MVP scale. Pinecone's free tier has the same latency with more ops overhead.
3. **SQL joins with RLS** — `WHERE namespace = $2` filters by company_id + doc_type in one query, enforced by Row-Level Security. A separate vector DB would need application-level tenant isolation.

---

## Decision 3: Shared-schema RLS over per-tenant databases

At MVP scale (< 100 tenants), per-tenant databases add operational cost with no measurable security benefit.

- **RLS enforcement**: `SET LOCAL app.current_company_id = $1` in `get_db()` → every query filtered by the PostgreSQL session variable → no cross-tenant data leakage possible at the DB layer.
- **Superuser bypass**: The `postgres` role has bypass policies for migrations and internal tooling. Application users connect as a restricted role.
- **Upgrade path**: If a customer requires data isolation guarantees, we can migrate their tenant to a dedicated schema or database without changing the application code.

---

## Decision 4: ECS Fargate over EKS

Fargate is serverless containers. EKS is a Kubernetes cluster we'd manage.

- **Ops overhead**: EKS requires cluster upgrades, node pool management, and CNI configuration — estimated 40 hrs/month for a 4-person team. Fargate has zero node management.
- **Same skills**: Both use Docker images pushed to ECR and IAM roles for AWS access. Fargate is a subset of that skill set.
- **Upgrade path**: Migrating from Fargate task definitions to EKS deployments is a 1-day operation when the team grows past 10 engineers and needs advanced scheduling.

---

## Decision 5: SSE over WebSockets for agent streaming

Agent output is strictly one-directional: server emits events, browser listens.

- **ALB compatibility**: AWS ALB supports SSE without sticky sessions. WebSocket connections require sticky sessions (ALB target group setting), which complicates horizontal scaling.
- **Native browser API**: `EventSource` is built into every browser since 2012. No library needed. Auto-reconnects on disconnect with the `Last-Event-ID` header.
- **Simplicity**: SSE is HTTP. Firewalls, proxies, and load balancers understand it. WebSockets require protocol upgrades that some enterprise networks block.

---

## Data Flow

### Strategy Generation (primary flow)
```
1. POST /api/v1/strategy/generate  (backend)
2. backend → INSERT strategies (status='generating')
3. backend → POST /run  (agents service)
4. agents: LangGraph graph.ainvoke(GTMState)
   ├── orchestrator_node → routes to research
   ├── research_node → Perplexity MCP → ResearchReport
   ├── strategy_node → GTMStrategy
   ├── content_node → ContentAsset[]
   └── brand_alignment_node → validated ContentAsset[]
5. agents → SSE events per node: AGENT_START, AGENT_PROGRESS, AGENT_COMPLETE
6. browser EventSource receives events → AgentProgress component updates
7. agents → UPDATE strategies (status='complete', payload=GTMStrategy JSON)
```

### Knowledge Ingestion
```
1. POST /api/v1/knowledge/upload  (backend)
2. Extract text: PDF via pypdf, DOCX via python-docx
3. Chunk: 512-word paragraphs with 50-word overlap
4. Embed: text-embedding-3-small → 1536-dim float[]
5. INSERT document_chunks with namespace="{company_id}:{doc_type}"
6. HNSW index auto-updates
```

### RAG Retrieval (brand alignment)
```
1. brand_alignment_node: query = content asset text
2. PgVectorRetriever.retrieve(query, namespace)
3. Embed query → cosine similarity search → top-5 chunks
4. Brand score + revision loop (max 2 iterations)
```
