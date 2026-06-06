# Epic 2 — Agent Implementation

**Goal:** Replace all stub nodes with real LangGraph agent implementations. Strategy generation works end-to-end with SSE streaming.

**Target branch:** `staging`

---

## PRs in this Epic

| PR | Title | Owner | Branch |
|---|---|---|---|
| #9 | Orchestrator node — real routing logic | Yousef | `epic-2/pr-9-orchestrator` |
| #10 | Research node — Perplexity MCP integration | Abdulrahem | `epic-2/pr-10-research` |
| #11 | Strategy node — GTM framework generation | Yousef | `epic-2/pr-11-strategy` |
| #12 | Content node — ColdIQ email + LinkedIn generation | Yousef | `epic-2/pr-12-content` |
| #13 | Brand alignment node — RAG scoring + revision loop | Abdulrahem | `epic-2/pr-13-brand` |
| #14 | Backend SSE endpoint — /strategy/generate/stream | Nawaf | `epic-2/pr-14-sse` |
| #15 | pm-skills LangChain tool wrappers | Yousef | `epic-2/pr-15-pm-skills` |
| #16 | ColdIQ LangChain tool wrappers | Yousef | `epic-2/pr-16-coldiq` |
| #17 | Strategy page — live SSE + AgentProgress | Bader | `epic-2/pr-17-strategy-ui` |
| #18 | Content + Knowledge pages | Bader | `epic-2/pr-18-content-ui` |

---

## Acceptance Criteria

- [ ] POST /api/v1/strategy/generate starts a real LangGraph run
- [ ] SSE events arrive at the browser in real time
- [ ] AgentProgress component shows running → complete per node
- [ ] ResearchReport, GTMStrategy, ContentAsset[] persisted to DB after run
- [ ] Brand alignment score > 0.0 on all content assets
- [ ] LangSmith traces visible in LangSmith Cloud dashboard
