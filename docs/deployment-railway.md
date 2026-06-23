# Railway Deployment — Postgres (pgvector) + Redis (PR #21)

> **Status:** ReachGTM deploys to **Railway** (backend, agents, Postgres, Redis)
> and **Cloudflare Pages** (frontend). This supersedes the AWS plan in
> `epic-3-deployment.md` (ECS/ECR/RDS/ElastiCache/S3/CloudFront).

This PR provisions the **data layer** — managed Postgres with pgvector and
managed Redis — and wires the Python services to them. The application code is
provider-agnostic: it only reads `DATABASE_URL` and `REDIS_URL`.

---

## Architecture

| Layer | Platform |
|---|---|
| Frontend (Next.js) | Cloudflare Pages |
| Backend (FastAPI) | Railway service (`backend/Dockerfile`) |
| Agents (LangGraph) | Railway service (`agents/Dockerfile`) |
| PostgreSQL + pgvector | Railway Postgres plugin (**pgvector image**) |
| Redis (rate limiter) | Railway Redis plugin |

Config-as-code lives in `infra/railway/backend.json` and
`infra/railway/agents.json`.

---

## 1. Create the Postgres database (with pgvector)

`init.sql` runs `CREATE EXTENSION vector` and builds an HNSW index, so the
database **must** use a Postgres image that ships pgvector.

1. In your Railway project: **New → Database → Add PostgreSQL**, choosing the
   **pgvector** template (Railway publishes one). The stock Postgres image may
   not include the `vector` extension — if `CREATE EXTENSION vector` fails, you
   are on the wrong image.
2. Railway exposes the connection string as the `DATABASE_URL` variable on the
   Postgres service.

### Apply the schema

Railway does not auto-run init scripts. Apply the schema once from your machine
(or a one-off Railway shell):

```bash
# Use the PUBLIC connection string from the Railway Postgres "Connect" tab
DATABASE_URL="postgresql://postgres:...@...railway.app:PORT/railway" \
  ./scripts/apply_migrations.sh
```

Verify:

```bash
psql "$DATABASE_URL" -c "\dx"   # expect: vector, uuid-ossp
psql "$DATABASE_URL" -c "\dt"   # expect: companies, users, sessions, ...
```

---

## 2. Create Redis

1. **New → Database → Add Redis.**
2. Railway exposes the connection string as `REDIS_URL` on the Redis service.

The rate limiter (`backend/app/middleware/rate_limit.py`) uses
`redis.asyncio.from_url(settings.redis_url)` — no code change needed.

---

## 3. Deploy the backend and agents services

Create two services from this repo, each pointing at its config file
(Service → Settings → **Config-as-code** → Config Path):

| Service | Config Path | Dockerfile |
|---|---|---|
| `reachgtm-backend` | `infra/railway/backend.json` | `backend/Dockerfile` |
| `reachgtm-agents` | `infra/railway/agents.json` | `agents/Dockerfile` |

Both Dockerfiles build with the **repo root** as context (they copy `shared/`),
so leave each service's root directory at the repository root.

Railway injects a `$PORT` at runtime; the config `startCommand` already binds
uvicorn to `$PORT`, and `healthcheckPath` is `/health` for both.

### Service variables

Set these on **both** the backend and agents services. Use Railway reference
variables so the DB/Redis URLs stay in sync:

| Variable | Value |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` |
| `OPENAI_API_KEY` | _your key_ |
| `JWT_SECRET` | _random 32+ char string_ |
| `LANGSMITH_API_KEY` | _optional_ |
| `PERPLEXITY_API_KEY` | _optional (agents)_ |
| `ENVIRONMENT` | `production` |

On the **backend** service also set `AGENTS_URL` to the agents service's private
URL (e.g. `http://${{reachgtm-agents.RAILWAY_PRIVATE_DOMAIN}}:8001`) so the SSE
endpoint can reach the agents service over Railway's private network.

---

## 4. Verify

```bash
curl https://<backend-domain>/health   # {"service":"backend","status":"ok"}
curl https://<agents-domain>/health     # {"service":"agents","status":"ok"}
```

The backend is healthy only once `DATABASE_URL`/`REDIS_URL` resolve, the schema
is applied, and `OPENAI_API_KEY`/`JWT_SECRET` are set.

---

## Acceptance (PR #21)

This PR ships the **config + scripts + docs**. The boxes below are verified
operationally once the Railway resources are provisioned by following the steps
above (they require a live Railway project, so they are not checked by CI):

- [ ] Managed Postgres with pgvector extension (HNSW index created by `init.sql`)
- [ ] Managed Redis connected (rate limiter operational)
- [ ] Services wired via `DATABASE_URL` / `REDIS_URL` — no application code change
