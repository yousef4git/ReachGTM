# Epic 1 — Foundation

**Goal:** Get the project to `docker compose up --build` with all health endpoints green and auth working end-to-end.

**Branch:** `epic-1/pr-1-scaffold` (single PR covers all 8 items below)

---

## PRs in this Epic

| PR | Title | Owner | Branch |
|---|---|---|---|
| #1 | Project scaffold — all directories, Docker, CI | Yousef | `epic-1/pr-1-scaffold` |
| #2 | Shared schemas (single PR for all 4 owners) | All | included in #1 |
| #3 | DB migration — init.sql, RLS, HNSW index | Nawaf | included in #1 |
| #4 | Auth endpoints — register, login, refresh, invite | Nawaf | included in #1 |
| #5 | Tenant middleware + rate limiter | Nawaf | included in #1 |
| #6 | LangGraph skeleton — 5 stub nodes + graph compile | Yousef | included in #1 |
| #7 | PgVector retriever (real implementation) | Abdulrahem | included in #1 |
| #8 | Frontend auth pages + AgentProgress component | Bader | included in #1 |

---

## Acceptance Criteria

- [ ] `docker compose -f infra/docker-compose.yml up --build` completes without error
- [ ] `GET http://localhost:8000/health` → `{"service":"backend","status":"ok"}`
- [ ] `GET http://localhost:8001/health` → `{"service":"agents","status":"ok"}`
- [ ] `GET http://localhost:3000` → HTML (redirects to /dashboard, no crash)
- [ ] `POST /api/v1/auth/register` with `{email, password, company_name}` → 201 + tokens
- [ ] `POST /api/v1/auth/login` → 200 + tokens
- [ ] `POST /api/v1/auth/refresh` with valid refresh token → 200 + new tokens
- [ ] DB has 8 tables: companies, users, sessions, knowledge_documents, document_chunks, strategies, content_assets, company_memory
- [ ] RLS enabled on all tenant tables — query without company_id returns 0 rows
- [ ] `pytest backend/tests/ -v` — all pass
- [ ] `pytest agents/tests/ -v` — all pass (graph compiles + runs stub nodes)
- [ ] CI passes on GitHub Actions (lint-python, test-backend, test-agents, lint-frontend)
