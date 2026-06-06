# ReachGTM — Agent Reference

## Graph Topology

```
START
  ↓
orchestrator ─────────────────────────────┐
  ↓ (no strategy exists)                  │ (strategy exists)
research                                  │
  ↓                                       │
strategy                                  │
  ↓                          ←────────────┘
content
  ↓
brand_alignment
  ↓
END
```

All nodes share `GTMState` (a Pydantic BaseModel with LangGraph message reducer).

---

## Node: orchestrator

**File:** `agents/app/graph/nodes/orchestrator.py`  
**Prompt:** `agents/app/prompts/orchestrator.py`

**Inputs from GTMState:**
- `messages` — user conversation history
- `research_report` — None if not yet run
- `gtm_strategy` — None if not yet generated

**Outputs to GTMState:**
- `current_agent: "orchestrator"`

**Routing logic:**
- `research_report is None` → route to `research`
- `gtm_strategy is None` → route to `strategy`
- content request + `gtm_strategy exists` → route to `content`

**MCP tools:** None  
**LangSmith tag:** `orchestrator`

---

## Node: research

**File:** `agents/app/graph/nodes/research.py`  
**Prompt:** `agents/app/prompts/research.py`

**Inputs from GTMState:**
- `messages` — contains the user's company description
- `metadata.company_profile` — structured company info

**Outputs to GTMState:**
- `research_report: ResearchReport`
- `current_agent: "research"`

**MCP tools:**
- `perplexity.search` — TAM/SAM/SOM, competitors, segments, signals

**Self-reflection:** Verifies that TAM/SAM/SOM are numeric with sources before passing to strategy.

**LangSmith tag:** `research`

---

## Node: strategy

**File:** `agents/app/graph/nodes/strategy.py`  
**Prompt:** `agents/app/prompts/strategy.py`

**Inputs from GTMState:**
- `research_report: ResearchReport`

**Outputs to GTMState:**
- `gtm_strategy: GTMStrategy`
- `current_agent: "strategy"`

**Skills applied:** pm-skills framework — positioning before channels, ICP before content

**MCP tools:** None (uses ResearchReport as context)

**LangSmith tag:** `strategy`

---

## Node: content

**File:** `agents/app/graph/nodes/content.py`  
**Prompt:** `agents/app/prompts/content.py`

**Inputs from GTMState:**
- `gtm_strategy: GTMStrategy`
- `metadata.content_types` — requested content types
- `metadata.count_per_type` — how many assets per type

**Outputs to GTMState:**
- `content_assets: list[ContentAsset]` (validation_status=PENDING)
- `current_agent: "content"`

**Skills applied:** ColdIQ methodology — 137 sales triggers, cold email sequences, LinkedIn hooks

**MCP tools:** None

**LangSmith tag:** `content`

---

## Node: brand_alignment

**File:** `agents/app/graph/nodes/brand_alignment.py`  
**Prompt:** `agents/app/prompts/brand_alignment.py`

**Inputs from GTMState:**
- `content_assets` — list from content node
- `company_id` — for RAG namespace lookup

**Outputs to GTMState:**
- `content_assets` — updated with `validation_status`, `brand_alignment_score`, `revision_notes`
- `current_agent: "brand_alignment"`

**RAG retrieval:**
- Tool: `PgVectorRetriever` (`agents/app/tools/retriever.py`)
- Namespace: `{company_id}:brand_guide`, `{company_id}:pitch_deck`
- Top-k: 5 chunks per query

**Self-reflection loop:** Max 2 revision iterations per asset. If score < 0.7 after 2 revisions, approve with notes.

**MCP tools:** None (uses pgvector via PgVectorRetriever)

**LangSmith tag:** `brand_alignment`

---

## SSE Event Schema

All events match `AgentEvent` in `shared/schemas.py`:

| Event | Emitted by | Data |
|---|---|---|
| `agent_start` | Each node on entry | `{agent: "research"}` |
| `agent_progress` | Long-running steps | `{agent: "research", message: "Searching TAM..."}` |
| `agent_output` | Node produces output | `{agent: "strategy", data: GTMStrategy}` |
| `agent_complete` | Node exits | `{agent: "brand_alignment"}` |
| `done` | Graph END | `{}` |
| `error` | Any node exception | `{message: "error text"}` |
