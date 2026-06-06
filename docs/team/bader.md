# Bader — Frontend Engineer Guide

**Your role:** Next.js 16 App Router, real-time SSE streaming UI, content and knowledge pages.

---

## Your PRs

| Epic | PR | Branch | Title |
|---|---|---|---|
| 2 | #17 | `epic-2/pr-17-strategy-ui` | Strategy page — live SSE + AgentProgress |
| 2 | #18 | `epic-2/pr-18-content-ui` | Content + Knowledge pages |
| 3 | #23 | `epic-3/pr-23-cdn` | CloudFront CDN for frontend |

---

## Local Setup

```bash
git clone https://github.com/yousef4git/ReachGTM.git
cd ReachGTM
cp .env.example .env
# Fill in: OPENAI_API_KEY, JWT_SECRET (any 32-char random string)
docker compose -f infra/docker-compose.yml up --build
```

Frontend runs at http://localhost:3000 — it will auto-reload on file changes (the Docker volume is mounted).

For faster iteration, run the frontend directly (outside Docker):
```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

---

## Codebase Orientation

The scaffold (already merged) gives you working stubs. Key files:

```
frontend/
├── app/                          # Pages — App Router (no pages/ directory)
│   ├── (auth)/login/page.tsx     # DONE — real login form
│   ├── (auth)/register/page.tsx  # DONE — real register form
│   ├── dashboard/page.tsx        # STUB — your job in PR #17
│   ├── strategy/new/page.tsx     # STUB — your job in PR #17
│   ├── strategy/[id]/page.tsx    # STUB — your job in PR #17
│   ├── content/page.tsx          # STUB — your job in PR #18
│   ├── knowledge/page.tsx        # STUB — your job in PR #18
│   └── research/page.tsx         # STUB — your job in PR #18
├── components/
│   ├── agent/AgentProgress.tsx   # DONE — timeline component, ready to use
│   ├── layout/Navbar.tsx         # STUB — wire up in PR #17
│   └── layout/Sidebar.tsx        # STUB — wire up in PR #17
├── hooks/
│   ├── useAgentStream.ts         # DONE — native EventSource SSE, ready to use
│   └── useAuth.ts                # DONE — login/register/logout
├── lib/
│   ├── api.ts                    # DONE — axios with auth interceptors
│   └── auth.ts                   # DONE — token helpers
├── types/index.ts                # DONE — all TypeScript types
└── store/useStore.ts             # DONE — Zustand store
```

---

## PR #17 — Strategy Page (Live SSE + AgentProgress)

**Branch:** `epic-2/pr-17-strategy-ui` (create from `staging`)

```bash
git checkout staging && git pull
git checkout -b epic-2/pr-17-strategy-ui
```

### What to build

**Depends on:** PR #14 (Nawaf's SSE endpoint) must be merged first, or you can mock the SSE stream locally.

**1. Strategy new page** (`frontend/app/strategy/new/page.tsx`)

A form where the user describes their company and starts the GTM strategy generation.

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAgentStream } from "@/hooks/useAgentStream";
import { AgentProgress } from "@/components/agent/AgentProgress";
import { strategyApi } from "@/lib/api";

export default function NewStrategyPage() {
  const router = useRouter();
  const { events, isStreaming, error, start } = useAgentStream();
  const [form, setForm] = useState({
    name: "", industry: "", stage: "seed", description: "",
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // 1. POST to /strategy/generate — get back session_id
    const { session_id } = await strategyApi.generate({
      company_profile: { ...form, stage: form.stage },
    });
    // 2. Start SSE stream
    start(session_id);
    // 3. When done, redirect to /strategy/[id]
    // (handle in useEffect watching events for DONE event)
  }

  return (
    <div className="max-w-2xl mx-auto p-8">
      {!isStreaming ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <h1 className="text-2xl font-bold">Generate GTM Strategy</h1>
          {/* form fields for name, industry, stage, description */}
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded">
            Generate Strategy
          </button>
        </form>
      ) : (
        <div>
          <h2 className="text-xl font-semibold mb-4">Generating your strategy...</h2>
          <AgentProgress events={events} />
          {error && <p className="text-red-500 mt-2">{error}</p>}
        </div>
      )}
    </div>
  );
}
```

**2. Strategy view page** (`frontend/app/strategy/[id]/page.tsx`)

Displays the completed GTMStrategy after agents finish.

**3. Dashboard page** (`frontend/app/dashboard/page.tsx`)

List of past strategies with a "New Strategy" button. Fetches from `GET /api/v1/strategy/` (wire up to Nawaf's API).

**4. Navbar + Sidebar** (`frontend/components/layout/`)

Replace the stubs with a real nav that shows:
- Logo / "ReachGTM"
- Links: Dashboard, Strategy, Content, Knowledge
- User email + logout button

Wrap all authenticated pages in a layout component that renders `<Navbar />` + `<Sidebar />`.

### Key pattern — watching SSE events for completion

```tsx
import { useEffect } from "react";
import { AgentEventType } from "@/types";

useEffect(() => {
  const done = events.find(
    (e) => e.event === AgentEventType.DONE || e.event === AgentEventType.AGENT_COMPLETE
  );
  if (done && done.data?.strategy_id) {
    router.push(`/strategy/${done.data.strategy_id}`);
  }
}, [events]);
```

### Testing the SSE stream locally (mock)

Before Nawaf's PR #14 merges, test with a local mock:

```bash
# In a terminal, serve a fake SSE stream
python3 -c "
import time, sys
events = [
  'data: {\"event\":\"agent_start\",\"agent\":\"research\",\"message\":\"Starting market research\"}\n\n',
  'data: {\"event\":\"agent_complete\",\"agent\":\"research\",\"message\":\"Research complete\"}\n\n',
  'data: {\"event\":\"agent_start\",\"agent\":\"strategy\",\"message\":\"Building GTM strategy\"}\n\n',
  'data: {\"event\":\"done\"}\n\n',
]
for e in events:
    print(e, end='', flush=True)
    time.sleep(1)
"
```

Point `NEXT_PUBLIC_API_URL` to your mock server, or stub `strategyApi.generate` to return a hardcoded session_id.

### PR checklist

- [ ] Strategy form submits and triggers SSE stream
- [ ] `AgentProgress` shows running → complete for each agent in real time
- [ ] Dashboard lists past strategies
- [ ] Navbar and sidebar render on all authenticated pages
- [ ] Redirects unauthenticated users to `/login`
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] No lint errors (`npm run lint`)

---

## PR #18 — Content + Knowledge Pages

**Branch:** `epic-2/pr-18-content-ui` (create from `staging`, ideally after PR #17 merges)

### Content page (`frontend/app/content/page.tsx`)

List of all `ContentAsset[]` for the company. Each card shows:
- Content type badge (Cold Email, LinkedIn Post, etc.)
- Title
- Validation status indicator (pending / approved / revised)
- Brand alignment score (0–1 as a percentage)
- "View" and "Copy" actions

Use the `ContentCard` component stub at `frontend/components/content/ContentCard.tsx` — flesh it out.

### Content create page (`frontend/app/content/create/page.tsx`)

Form to generate content for a specific strategy:
- Select strategy (dropdown from `GET /api/v1/strategy/`)
- Select content types (checkboxes: cold email, LinkedIn post, blog outline, ad copy)
- Count per type (1–5)
- Submit → `POST /api/v1/content/generate`

### Knowledge page (`frontend/app/knowledge/page.tsx`)

File upload UI for brand guides, pitch decks, case studies:
- Drag-and-drop file upload (accept `.pdf`, `.docx`)
- Document type selector (dropdown)
- Upload progress indicator
- List of uploaded documents with status (pending / indexed / failed)

```tsx
import { knowledgeApi } from "@/lib/api";

async function handleUpload(file: File, docType: string) {
  const result = await knowledgeApi.upload(file, docType);
  // result: { document_id, chunks, status }
}
```

### PR checklist

- [ ] Content list renders with real API data
- [ ] ContentCard shows type, status, and alignment score
- [ ] Knowledge upload works end-to-end (file → indexed in DB)
- [ ] Document list shows status updates
- [ ] No TypeScript errors
- [ ] PR targets `staging`, reviewer: @yousefalshuwayi

---

## PR #23 — CloudFront CDN

**Branch:** `epic-3/pr-23-cdn` (create from `staging` after Epic 2 completes)

### What to build

CloudFront distribution in front of the ECS frontend service (or serving Next.js static assets from S3).

**Files to create:**
- `infra/terraform/cloudfront.tf`

```hcl
resource "aws_cloudfront_distribution" "frontend" {
  origin {
    domain_name = aws_lb.frontend.dns_name  # ALB in front of ECS
    origin_id   = "frontend-alb"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = ""

  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "frontend-alb"
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = true
      cookies { forward = "all" }
      headers = ["Authorization"]
    }
    min_ttl     = 0
    default_ttl = 0  # Don't cache Next.js HTML — it's dynamic
    max_ttl     = 0
  }

  # Cache Next.js static assets aggressively
  ordered_cache_behavior {
    path_pattern     = "/_next/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "frontend-alb"
    viewer_protocol_policy = "redirect-to-https"
    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
    min_ttl     = 86400
    default_ttl = 86400
    max_ttl     = 31536000
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    cloudfront_default_certificate = true  # replace with ACM cert for custom domain
  }
}
```

### PR checklist

- [ ] CloudFront distribution created via `terraform apply`
- [ ] Frontend accessible at CloudFront URL with HTTPS
- [ ] `/_next/static/*` assets cached at edge
- [ ] HTML pages not cached (dynamic Next.js content)
- [ ] ALB security group only accepts traffic from CloudFront IP ranges

---

## Branch Rules

```
main (protected — never push here directly)
  ↑ PR from staging only
staging (default — all your PRs go here)
  ↑ PR from your feature branch
epic-2/pr-17-strategy-ui  ← your branch
```

**Every PR:**
1. `git checkout staging && git pull`
2. `git checkout -b epic-N/pr-N-<name>`
3. Implement → commit → push
4. `gh pr create --base staging`
5. Tag @yousefalshuwayi as reviewer

---

## Questions

- Coordinate with Nawaf on the SSE event format — specifically the `DONE` event shape, so you know what `done.data` contains (e.g. `strategy_id`).
- Coordinate with Yousef on the overall `AgentEvent` data payload — the `data` field differs per agent.
