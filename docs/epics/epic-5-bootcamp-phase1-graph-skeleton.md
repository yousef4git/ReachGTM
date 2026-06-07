# Epic 5 — Bootcamp Phase 1: Graph Skeleton (All Together)

**Goal:** Every team member sees the LangGraph core built from scratch. No silos. Pair-program on one machine.

**Branch:** `epic-5/pr-0-graph-skeleton`

**Owner:** All 4 — pair-programmed together

---

## PRs in this Epic

| PR | Title | Owner | What Each Person Learns |
|----|-------|-------|------------------------|
| #0 | LangGraph skeleton — state, graph, node stubs, compile | All 4 paired | LangGraph StateGraph, state typing, conditional edges, async nodes |

---

## Tasks inside PR #0

- [ ] Define `GTMState` Pydantic model with all fields (messages, research_report, gtm_strategy, content_assets, metadata, current_agent)
- [ ] Wire 5 stub nodes: orchestrator → research → strategy → content → brand_alignment
- [ ] Implement conditional routing in orchestrator (no strategy → research; has strategy → content)
- [ ] Each node stub logs its name and returns dummy output
- [ ] `python -c "from agents.app.graph.graph import build_graph; g = build_graph(); print('Graph compiled OK')"` passes
- [ ] All 4 commit as co-authors in the PR description
- [ ] Graph compiles and runs end-to-end with dummy data via CLI test

## Acceptance Criteria

- [ ] LangGraph StateGraph compiles without errors
- [ ] Running the graph with dummy input visits all 5 nodes in order
- [ ] orchestrator conditionally routes to research (no strategy) vs content (has strategy)
- [ ] Each team member can explain the graph topology and state flow
