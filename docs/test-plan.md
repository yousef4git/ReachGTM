# ReachGTM — Test Plan

**Status:** Living document. Owned by the whole team; changes follow the same review rules as `shared/schemas.py`.
**Goal:** Define what "tested" means for every layer of ReachGTM so each PR ships with the right tests and CI stays green.

---

## 1. Objectives

1. Catch regressions before they reach `staging` (and never let them reach `main`).
2. Prove the **agent pipeline** (research → strategy → content → brand) runs end-to-end without burning real LLM/MCP credits in CI.
3. Guarantee **multi-tenant isolation** — no tenant can ever read another tenant's rows (RLS).
4. Keep the `shared/schemas.py` ↔ `frontend/types/index.ts` contract in sync.
5. Make tests fast and deterministic so the bootcamp's parallel PRs don't block on flaky CI.

---

## 2. Test Pyramid

```
            ▲  fewer, slower, most realistic
   E2E      │  Playwright: register → upload → generate → view (1 happy path + 1 auth-guard)
   ─────────┤
 Integration│  API + DB(+RLS) + Redis + full graph (stubbed LLM/MCP via cassettes) + SSE
   ─────────┤
   Unit     │  pure functions, single nodes, prompts, React components, schema validation
            ▼  many, fast, isolated
```

Rule of thumb: **every PR adds unit tests; node/endpoint PRs add an integration test; UI PRs add a component test.** E2E is owned centrally (see PR #20 / smoke tests).

---

## 3. Tooling by Layer

| Layer | Runner | Key libs | Where |
|---|---|---|---|
| Backend (FastAPI) | `pytest` + `pytest-asyncio` | `httpx.AsyncClient`, `asyncpg`, `fakeredis` | `backend/tests/` |
| Agents (LangGraph) | `pytest` + `pytest-asyncio` | `vcrpy`/cassettes, `respx` (HTTP mock) | `agents/tests/` |
| Shared schemas | `pytest` | `pydantic` round-trip | `tests/contract/` (new) |
| Frontend (Next.js) | `vitest` + React Testing Library | `@testing-library/react`, `msw` | `frontend/__tests__/` (new) |
| E2E | `playwright` | `@playwright/test` | `frontend/e2e/` (new) |
| Lint/Types | `ruff`, `mypy`, `eslint`, `tsc` | — | CI (already wired) |

> **Version policy:** per `CLAUDE.md`, never hardcode versions — resolve latest stable via context7 before adding any test dep to `requirements.txt` / `package.json`.

---

## 4. Environments

| Env | Used for | Notes |
|---|---|---|
| Local Docker Compose | manual + integration | `docker compose -f infra/docker-compose.yml up`; Postgres has pgvector + RLS, Redis for rate limit |
| CI (GitHub Actions) | every push + PR to staging/main | `pgvector/pgvector:pg16` service container; **no real API keys** — all external calls mocked |
| Staging | smoke tests post-deploy | real services, synthetic tenant |
| Production | smoke tests post-deploy | read-only health + 1 synthetic generate, then cleanup |

**No test ever calls the real OpenAI / Perplexity / Databar / Attio APIs.** CI sets `OPENAI_API_KEY=test`; agents replay recorded cassettes.

---

## 5. Test Types & What They Cover

### 5.1 Unit

**Backend**
- `auth_service`: password hashing, JWT claims (company_id/sub/role), token expiry, refresh rotation. *(partly exists: `test_auth.py`)*
- `middleware`: JWT → `company_id` extraction; rate limiter sliding-window math (100 req/min) with `fakeredis`.
- `services`: `knowledge_service` chunking (512-word chunks), `storage_service` key generation.

**Agents**
- Each node in isolation with a hand-built `GTMState` and a stubbed LLM/tool — assert it sets `current_agent` and writes its output field. *(graph compile + stub run exists: `test_graph.py`)*
- Orchestrator routing table: given state, asserts next node (no research → research; strategy exists → content).
- Brand-alignment scoring: score < 0.7 triggers one revision; max 2 revisions then approve.
- Prompt files: load + render with sample vars, assert required sections present.

**Frontend**
- `useAgentStream` SSE hook: parses events, transitions node status running → complete.
- `AgentProgress` component: renders per-node state.
- `axios` API client: attaches auth header, refreshes on 401.

### 5.2 Integration

- **API + DB**: spin real Postgres (CI service), run `init.sql`, exercise `register → login → refresh` over `httpx.AsyncClient`; assert 201/200 + token shape.
- **RLS / multi-tenancy** *(critical)*: insert rows for tenant A and B; with `SET LOCAL app.current_company_id = A`, a query returns only A's rows; without it, **0 rows**. Repeat for every tenant table (companies, users, sessions, knowledge_documents, document_chunks, strategies, content_assets, company_memory).
- **pgvector retriever**: insert chunks with 1536-dim embeddings, query HNSW, assert nearest-neighbour ordering.
- **Full graph**: `graph.ainvoke()` with **cassette-backed** LLM + Perplexity → asserts ResearchReport, GTMStrategy, ContentAsset[] produced and persisted; brand score > 0.0. *(PR #20 — integration + cassette tests.)*
- **SSE endpoint**: `POST /strategy/generate/stream`, read the event stream, assert ordered `node_start`/`node_complete` events and a terminal `done`.

### 5.3 Contract

- Round-trip every model in `shared/schemas.py` (serialize → deserialize → equal).
- Snapshot the JSON Schema of each Pydantic model; diff against `frontend/types/index.ts` shape. Fails the build if a backend model changes without the matching TS update (enforces the CLAUDE.md rule).

### 5.4 End-to-End (Playwright)

1. **Happy path**: register → redirected to `/knowledge` → upload a small brand PDF → `/strategy` generate → AgentProgress completes → strategy + content rendered.
2. **Auth guard**: unauthenticated visit to `/dashboard` → redirected to login.

### 5.5 Non-Functional

| Concern | Test |
|---|---|
| Security — authz | role matrix: member cannot invite; only owner is admin (see README roles table) |
| Security — tenancy | RLS isolation suite (5.2) is the gate |
| Security — input | malformed JWT, expired token, SQL-ish payloads rejected with 401/422 |
| Rate limiting | 101st request in a minute for a tenant → 429 |
| Performance | strategy generate p95 budget (record from LangSmith); pgvector query < 50 ms on seed set |
| Observability | run produces a LangSmith trace with expected node tags (manual/staging check) |

---

## 6. Test Data & Fixtures

- **Cassettes**: record LLM + MCP responses once (real keys, local), commit sanitized cassettes under `agents/tests/cassettes/`. CI replays them. Re-record only when a prompt/tool contract changes.
- **Seed tenants**: `conftest.py` fixture creates 2 companies + users for isolation tests, torn down per test (transaction rollback).
- **Sample assets**: tiny PDF/DOCX fixtures for knowledge upload; canned `ResearchReport`/`GTMStrategy`/`ContentAsset` example instances live in `shared/schemas.py` (the same stubs PR #8 returns) so unit and integration tests share shapes.
- **Secrets**: never commit real keys; CI uses dummy values; cassettes must be scrubbed of tokens.

---

## 7. Coverage Targets & Gates

| Scope | Target | Gate |
|---|---|---|
| Backend services + middleware | ≥ 80% line | PR blocked below |
| Agent nodes + routing | ≥ 75% line | PR blocked below |
| RLS isolation suite | 100% of tenant tables | hard gate (any miss fails) |
| Contract (schemas ↔ types) | all models | hard gate |
| Frontend critical hooks/components | smoke + key paths | warn, then enforce |

Coverage measured with `pytest --cov` and `vitest --coverage`. Targets ramp as suites grow; RLS + contract are hard gates from day one.

---

## 8. CI Integration

Current jobs in `.github/workflows/ci.yml`: `lint-python`, `test-backend`, `test-agents`, `lint-frontend`. Proposed additions:

| Job | Status | Action |
|---|---|---|
| `lint-python` (ruff + mypy) | ✅ exists | keep |
| `test-backend` (pytest + pgvector service) | ✅ exists | add `--cov`, RLS + rate-limit suites |
| `test-agents` (pytest) | ⚠️ exists but **no Postgres/Redis service** attached though `DATABASE_URL`/`REDIS_URL` are set | add service containers OR keep node tests DB-free with cassettes |
| `lint-frontend` (eslint + tsc) | ✅ exists | keep |
| `test-frontend` (vitest) | ❌ missing | **add** |
| `test-contract` (schemas ↔ types) | ❌ missing | **add** |
| `e2e` (Playwright, on PR to main only) | ❌ missing | **add**, gated to main to keep PR CI fast |

All test jobs run on push to any branch and PRs to `staging`/`main`, matching the current trigger.

---

## 9. Per-PR Testing Checklist

Tie to the bootcamp rotation (`docs/rotation_plan_v2.md`). Author proves these before requesting review; reviewer verifies.

- [ ] New code has unit tests; `pytest`/`vitest` pass locally.
- [ ] LangGraph node PR: node test against a **stub** input + at least one routing assertion.
- [ ] Endpoint PR: integration test over `httpx.AsyncClient` (+ RLS assertion if it touches tenant tables).
- [ ] UI PR: component/hook test; no `eslint`/`tsc` errors.
- [ ] Touches `shared/schemas.py`: updated `frontend/types/index.ts` **and** contract test in the same PR.
- [ ] No real external API calls added; new fixtures/cassettes committed and scrubbed.
- [ ] `docker compose up --build` healthchecks still green.
- [ ] CI green on the branch.

---

## 10. Mapping to Epic Acceptance Criteria

| Epic | Acceptance criterion | Covering test |
|---|---|---|
| 1 | health endpoints 200 | integration smoke (`/health` ×3) |
| 1 | register/login/refresh | `test_auth` unit + API integration |
| 1 | 8 tables exist + RLS | migration test + RLS isolation suite |
| 1 | graph compiles + stub run | `test_graph.py` |
| 2 | real graph run, events stream | full-graph cassette test + SSE test (PR #20, #14) |
| 2 | assets persisted, brand score > 0 | integration assertion on DB after run |
| 2 | LangSmith traces | staging observability check |
| 3 | prod deploy, SSL, RDS/ElastiCache | production smoke suite (PR #25) |
| 3 | zero-downtime deploy | rolling-update smoke check |
| 4 | Phase-2 features | per-feature tests as issues are picked up |

---

## 11. Known Gaps (backlog)

1. **No frontend tests yet** — only `eslint` + `tsc`. Add `vitest` + RTL (`test-frontend` job).
2. **No E2E** — add Playwright happy path + auth guard.
3. **No RLS isolation suite** — highest priority; multi-tenancy is a core guarantee.
4. **No contract test** — schemas/types drift is currently only caught by review.
5. **`test-agents` CI** references `DATABASE_URL`/`REDIS_URL` with no service containers — either attach services or keep agent tests fully cassette/DB-free.
6. **No coverage reporting** — wire `--cov` and publish in CI.

---

## 12. Definition of Done (project-level)

A feature is "done" when: unit + integration tests exist and pass in CI, tenant tables it touches are covered by the RLS suite, any schema change is mirrored in TS with a contract test, the relevant epic acceptance criterion has a mapped test, and `docker compose up --build` stays green.
