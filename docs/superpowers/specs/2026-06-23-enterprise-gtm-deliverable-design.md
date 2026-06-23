# ReachGTM — Enterprise GTM Deliverable, Knowledge RAG & Company Chatbot

**Date:** 2026-06-23
**Author:** Yousef (architecture lead) + Claude
**Status:** Approved (autonomous execution)

## Goal

Turn ReachGTM from a "pipeline that produces ephemeral output" into an enterprise-usable
GTM deliverable platform:

1. **Durable, DB-backed outputs** — generated strategy + content persist to Postgres and
   appear on the Content page (and survive any device / refresh / teammate).
2. **First-class knowledge ingestion** — ingest PPTX in addition to PDF/DOCX (+ TXT/MD),
   and actually *use* the knowledge base via RAG (fixing the retrieval bug).
3. **Company chatbot** — a streaming RAG assistant that answers grounded in everything the
   company has: knowledge base, generated strategy, content library, and company memory.
4. **Seeded demo** — Northwind Labs (B2B data-infra SaaS) mock company end-to-end, verified
   in loops.

## Current State (verified by exploration)

- **Ingestion already exists**: `knowledge_service.ingest_document` → extract (PDF/DOCX) →
  chunk (512w/50 overlap) → embed (`text-embedding-3-small`) → `document_chunks` (pgvector,
  HNSW). `GET /knowledge/` is real.
- **RAG retriever exists but is dead code**: `PgVectorRetriever` is never passed into the
  graph. **Bug:** ingestion stores `namespace = "{company_id}:{doc_type}"` but the retriever
  queries `WHERE namespace = "{company_id}"` → always returns 0 rows.
- **Persistence gap**: `content_assets` table exists but is never written. The SSE strategy
  stream is relayed byte-for-byte and never saved. `GET /content/` returns a hardcoded `[]`.
  Frontend persists to localStorage as the only durable store.
- **Chatbot**: `/agent` page is an "Epic 2" placeholder. `POST /chat/` just re-runs the
  agent pipeline (not a Q&A assistant).
- Backend owns Postgres (asyncpg pool + RLS via `app.current_company_id`); agents service is
  stateless but *does* have `database_url` configured.

## Design

### Phase 1 — DB-backed persistence (backbone)

- **`agent_stream.py` (backend relay)** becomes the persistence seam. It already proxies the
  agents SSE stream; we parse frames as they pass through, capture the `agent_complete`
  bundle (`gtm_strategy`, `content_assets`, `research_report`), and on terminal `done`:
  - acquire a pool connection, set tenant context, INSERT `strategies` (payload = full
    bundle) and one `content_assets` row per asset (linked to the new `strategy_id`),
  - emit a new `persisted` SSE event carrying `{strategy_id, content_ids}` *before* `done`,
  - then pass `done` through. Persistence failures never break the stream (best-effort,
    logged, surfaced as a non-fatal note).
- **New SSE event type** `persisted` added to `AgentEventType` (shared schema + TS type).
- **`content_service.py`**: add `list_content(conn, company_id)` and
  `persist_content_assets(conn, company_id, strategy_id, assets)`.
- **`strategy_service.py`**: add `persist_bundle(conn, company_id, user_id, session_id, bundle)`
  returning the new strategy id; `list_strategies(conn, company_id)`.
- **API**: `GET /content/` → real DB rows; add `GET /strategy/` list. `GET /strategy/{id}`
  already real.
- **Frontend**: `useAgentStream` captures `persisted` → store keeps `strategy_id`; Content
  page + hooks prefer backend rows (already coded to). localStorage demoted to a cache.

### Phase 2 — Ingestion + working RAG

- **PPTX/TXT/MD** added to `_extract_text` (PPTX via `python-pptx==1.0.2`: slides → shapes →
  text frames + tables; TXT/MD decoded directly). Frontend knowledge dropzone accepts the
  new types.
- **Fix retrieval**: retrieve by `company_id` (RLS-scoped) instead of the mismatched
  `namespace`. Optional `doc_type` filter retained.
- **Wire retriever into the graph**: agents `main.py` lifespan creates an asyncpg pool and a
  process-global `PgVectorRetriever` via a small registry; `brand_alignment_node` uses it
  (grounding content validation in real brand docs).

### Phase 3 — Company chatbot (RAG)

- **`chat_service.py` (backend)**: `retrieve_context` (embed question → vector search the
  company's chunks) + gather latest strategy payload, recent content, and company memory →
  build a grounded prompt → stream completion from **`gpt-5.4-mini`** (new
  `settings.chat_model`) as SSE tokens, ending with a `sources` payload.
- **`POST /chat/`** rewritten as a real streaming RAG endpoint (message in body; auth via
  TenantMiddleware Authorization header; consumed by frontend `fetch` + ReadableStream).
- **`/agent` page** rebuilt (frontend-design skill) into a real chat UI in the Command Desk
  aesthetic: message thread, streaming answer, grounded-source chips, suggested prompts.

### Phase 4 — Seed Northwind Labs + verification loop

- Seed script registers Northwind Labs, uploads mock KB docs (incl. a `.pptx` sales deck),
  runs a strategy generation (persisted), and confirms content + chat work.
- Verify in loops via the running stack (curl + browser): generation persists → Content page
  shows rows → chat answers cite KB + strategy. Iterate on any failure.

## Contracts touched (normally 4-reviewer per CLAUDE.md — flagged)

- `shared/schemas.py`: add `AgentEventType.PERSISTED`. Mirror in `frontend/types/index.ts`.
- `backend/config.py`: add `chat_model = "gpt-5.4-mini"`.
- `backend/requirements.txt`: add `python-pptx==1.0.2`.

## Risks / Notes

- `gpt-5.4-mini` is used verbatim per direction; isolated behind `settings.chat_model` so it
  is a one-line change if the id differs in this environment.
- RLS: backend connects as a role that the superuser-bypass policy covers; tenant config is
  still set on each persistence connection for correctness.
- Persistence is best-effort and must never break the user-facing stream.
