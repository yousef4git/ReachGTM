# Epic 3 — Production Deployment

**Goal:** Deploy frontend to Cloudflare Pages, backend/agents/db/redis to Railway.
Production deploys trigger on push to `main`.

---

## PR #23 — Cloudflare Pages Frontend (Bader)

**Owner:** Bader
**Branch:** `epic-3/pr-23-cloudflare-pages`

Replaces the legacy AWS CloudFront plan. The frontend (Next.js) is built as a static export and deployed to Cloudflare Pages with SPA fallback for dynamic routes.

### What changed

| File | Change |
|------|--------|
| `frontend/next.config.ts` | `output: "export"` + `images.unoptimized: true` |
| `frontend/app/strategy/[id]/page.tsx` | Added `generateStaticParams` returning `[]` (SPA fallback) |
| `frontend/wrangler.toml` | New — Cloudflare Pages project config |
| `frontend/public/_redirects` | New — SPA fallback for `/strategy/*` and `/content/create` |
| `frontend/package.json` | Added `deploy` script |
| `.github/workflows/deploy-frontend.yml` | New — Cloudflare Pages deploy on push to `main` |

### Prerequisites (one-time Cloudflare setup)

1. **Create a Cloudflare account** at https://dash.cloudflare.com/sign-up
2. **Enable Cloudflare Pages** — select your Free plan
3. **Get your Account ID** from the Cloudflare dashboard URL (`dash.cloudflare.com/?to=/:account/workers`)
4. **Create an API token** with `Cloudflare Pages:Edit` permission:
   - Dashboard → My Profile → API Tokens → Create Token
   - Use the "Cloudflare Pages" template
   - Set permission to `Cloudflare Pages:Edit`
5. **Set GitHub Actions secrets** in the repo:
   - `CLOUDFLARE_API_TOKEN` — token from step 4
   - `CLOUDFLARE_ACCOUNT_ID` — account ID from step 3
   - `NEXT_PUBLIC_API_URL` — Railway backend URL (e.g. `https://reachgtm-backend.railway.app`)

### Verify the build locally

```bash
cd frontend
npm ci
NEXT_PUBLIC_API_URL=https://reachgtm-backend.railway.app npm run build
ls out/   # Should show index.html, dashboard.html, login.html, ...
```

The `out/` directory is what gets deployed to Cloudflare Pages.

### Acceptance

- [ ] `git push origin main` triggers `deploy-frontend.yml` and updates Cloudflare Pages
- [ ] Frontend reachable at `<project>.pages.dev` or custom domain with valid SSL
- [ ] All pages load correctly: login, dashboard, strategy list, strategy detail, content, agent, knowledge
- [ ] Dynamic route `/strategy/<id>` loads via SPA fallback (no 404)
- [ ] SSE streaming on the strategy generate page works via `NEXT_PUBLIC_API_URL`

---

## Other Epic 3 Work (for reference)

| Service | Platform | Status |
|---------|----------|--------|
| Frontend (Next.js) | **Cloudflare Pages** (this PR) | In progress |
| Backend (FastAPI) | Railway | Done |
| Agents (LangGraph) | Railway | Done |
| PostgreSQL + pgvector | Railway Postgres plugin | Done |
| Redis | Railway Redis plugin | Done |

See `docs/deployment-railway.md` for the Railway setup steps.
