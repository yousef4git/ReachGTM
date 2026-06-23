# ReachGTM Bootcamp — Rotation Plan (v2, merged)

**Goal:** Equal learning across all 4 members in 3 weeks. Everyone writes at least one LangGraph node, one prompt file, touches Docker/infra, and reviews at least one peer PR.

> **What changed from v1** (the three gaps + a rebalance):
> 1. **Stub-driven parallelism in Week 2** — a shared state schema + stub nodes (new PR #8) lets people build against fakes instead of waiting for the previous node to merge. Week 2 is no longer a strict chain.
> 2. **Real infra PR** — `docker-compose` + `.env` + healthchecks is now PR #7 with a named author and reviewer, not a vague "everyone pairs."
> 3. **Named integration + testing task** — wiring the four nodes together and proving the full graph runs is now PR #20, owned, not nobody's job.
> 4. **Reviewer table cleaned up** — no self-reviews, every PR has exactly one or two named reviewers.

---

## Principle (unchanged)

No silos. Everyone learns:
- **LangGraph** — writes at least 1 node
- **Prompt engineering** — writes or improves at least 1 prompt file
- **Docker / local dev** — everyone touches `docker-compose.yml` (each adds their own service's healthcheck)
- **Code review** — peer rotation, not Yousef-only

---

## PR Distribution

### Yousef — Architecture → stretch into testing
| PR | Title | LangGraph? | Note |
|---|---|---|---|
| #8 | **Shared `GTMState` schema + stub nodes** *(new)* | ✅ Defines the contract | Unblocks everyone — Week 2 parallelism depends on this landing first |
| #9 | Orchestrator node — sets the node pattern | ✅ Writes first real node | Teaches the others by example |
| #20 | **Integration + cassette tests** *(new, his stretch)* | ✅ Wires all 4 nodes | Forces understanding of every node; learns testing |
| Review | Nawaf's #11 (strategy), Nawaf's #14 (SSE) | ✅ Peer review | |

### Abdulrahem — ML / RAG
| PR | Title | LangGraph? | Note |
|---|---|---|---|
| #10 | Research node — Perplexity MCP integration | ✅ Writes node | |
| #13 | Brand alignment node — RAG + revision loop | ✅ Writes second node | Builds against a **stubbed** `ContentAsset` (doesn't wait for #12) |
| Review | Bader's #12 (content), Bader's #17 (UI) | ✅ Peer review | |

### Nawaf — Backend → LangGraph
| PR | Title | LangGraph? | Note |
|---|---|---|---|
| #7 | **Infra: docker-compose + .env + healthchecks** *(new, named owner)* | ❌ Infra | Pairs with the team but Nawaf authors |
| #15 | pm-skills tool wrappers (ICP, positioning) | ❌ Tools (used in graph) | Warm-up before his node |
| #11 | Strategy node — GTM framework generation | ✅ First LangGraph node | Builds against a **stubbed** `ResearchReport` |
| #14 | SSE streaming endpoint — backend wiring | ❌ FastAPI | |
| Review | Abdulrahem's #13 (brand) | ✅ Peer review | |

### Bader — Frontend → LangGraph
| PR | Title | LangGraph? | Note |
|---|---|---|---|
| #16 | ColdIQ tool wrappers (email, LinkedIn) | ❌ Tools (used in graph) | Warm-up before his node |
| #12 | Content node — cold email + LinkedIn generation | ✅ First LangGraph node | Builds against a **stubbed** `GTMStrategy` |
| #17 | Strategy UI — live SSE streaming page | ❌ Next.js | Needs #14 |
| #18 | Content library + asset editor page | ❌ Next.js | Needs #14 |
| Review | Yousef's #9 (orchestrator) | ✅ Peer review | |

> **Load note:** node PRs are heavier than tool-wrapper or UI PRs. Yousef (3 PRs) and Abdulrahem (2 node PRs) carry the heaviest *graph* work; Nawaf and Bader carry more but lighter pieces. Roughly even by effort, not just count.

---

## Week-by-Week Timeline

### Week 1 — Foundation (fully parallel, no blocking)

```
Yousef     → PR #8  (shared schema + stub nodes)  — the contract everyone builds against
Yousef     → PR #9  (orchestrator)                — graph structure + /run, sets node pattern
Abdulrahem → PR #10 (research node)               — Perplexity MCP client + ResearchReport
Nawaf      → PR #7  (docker-compose + .env)        — infra everyone runs on
Nawaf      → PR #15 (pm-skills tools)              — tool wrappers, no deps
Bader      → PR #16 (coldiq tools)                 — tool wrappers, no deps
ALL        → review the shared schema (#8) together before building on it
```

**Week 1 ends when:** the shared schema is merged (#8), `docker compose up` works (#7), and orchestrator + research nodes run end-to-end (#9 + #10).

### Week 2 — Pipeline assembly (now 3 parallel tracks, not a chain)

```
Nawaf      → PR #11 (strategy node)   — builds against STUBBED ResearchReport from #8
Bader      → PR #12 (content node)    — builds against STUBBED GTMStrategy from #8
Abdulrahem → PR #13 (brand node)      — builds against STUBBED ContentAsset from #8
Nawaf      → PR #14 (SSE endpoint)    — needs #9, runs in parallel
```

> Because each node is written against a stub from #8, **none of these three wait for the others to merge.** They integrate at the end of the week, not sequentially through it.

**Week 2 ends when:** all four nodes exist and pass their own tests against stubs.

### Week 3 — Integration, UI, Polish

```
Yousef     → PR #20 (integration + cassette tests) — swap stubs for real nodes; prove full graph runs
Bader      → PR #17 (strategy UI)                  — needs #14
Bader      → PR #18 (content library UI)           — needs #14
TBD        → PR #19 (ECS cluster)                  — optional stretch, whoever wants AWS
ALL        → smoke tests, demo prep, README
```

**Week 3 ends with:** the full graph runs research → strategy → content → brand end-to-end (#20 green), surfaced live in the UI, demoed on local Docker Compose.

---

## Peer Review Rotation (cleaned up — no self-reviews)

| PR # | Title | Author | Reviewer(s) |
|---|---|---|---|
| #7 | docker-compose + infra | Nawaf | Abdulrahem |
| #8 | shared schema + stubs | Yousef | Nawaf + Bader |
| #9 | orchestrator node | Yousef | Bader |
| #10 | research node | Abdulrahem | Nawaf |
| #11 | strategy node | Nawaf | Yousef + Abdulrahem |
| #12 | content node | Bader | Abdulrahem |
| #13 | brand alignment node | Abdulrahem | Nawaf |
| #14 | SSE endpoint | Nawaf | Yousef |
| #15 | pm-skills tools | Nawaf | Bader |
| #16 | coldiq tools | Bader | Abdulrahem |
| #17 | strategy UI | Bader | Abdulrahem |
| #18 | content library UI | Bader | Yousef |
| #20 | integration + tests | Yousef | Bader + Nawaf |
| #19 | ECS (optional) | TBD | TBD |

Yousef is a **secondary reviewer** on architecture-critical PRs (#11, #14), not the sole gatekeeper. The shared schema (#8) gets two reviewers because everyone depends on it.

---

## Checklist for Fairness

- [ ] Everyone writes at least 1 LangGraph node → ✅ Yousef #8/#9, Abdulrahem #10/#13, Nawaf #11, Bader #12
- [ ] Everyone writes at least 1 prompt file → ✅ each node carries its own prompt
- [ ] Everyone touches Docker/infra → ✅ Nawaf authors #7; each member adds their service's healthcheck in their PR
- [ ] Everyone reviews at least 1 peer PR → ✅ (see rotation table)
- [ ] No single person is the critical-path bottleneck → ✅ **fixed via #8 stubs** — Week 2 nodes build in parallel against fakes
- [ ] Integration + testing is owned, not orphaned → ✅ PR #20 (Yousef)
- [ ] The person who knows LangGraph also learns something new → ✅ Yousef stretches into integration testing

---

## The two coordination rules that make this work

1. **#8 lands before any Week 2 node starts.** The shared `GTMState` + stub objects are the contract. If they're not merged and agreed, the parallelism collapses back into v1's chain. This is the single most important sequencing rule.
2. **Stubs return the example instances from #8.** Each node author builds against the same fake `ResearchReport` / `GTMStrategy` / `ContentAsset` so when #20 swaps stubs for real nodes, the shapes already match. Integration becomes wiring, not debugging.
