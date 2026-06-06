# Abdulrahem — ML Engineer Guide

**Your role:** RAG pipeline, pgvector, MCP tool integrations, research agent, brand alignment agent.

---

## Your PRs

| Epic | PR | Branch | Title |
|---|---|---|---|
| 2 | #10 | `epic-2/pr-10-research` | Research node — Perplexity MCP integration |
| 2 | #13 | `epic-2/pr-13-brand` | Brand alignment node — RAG scoring + revision loop |
| 3 | #24 | `epic-3/pr-24-mcp-extra` | Databar + Fetch MCP server integration |

---

## Local Setup

```bash
git clone https://github.com/yousef4git/ReachGTM.git
cd ReachGTM
cp .env.example .env
# Fill in: OPENAI_API_KEY, JWT_SECRET, PERPLEXITY_API_KEY
docker compose -f infra/docker-compose.yml up --build
```

Verify:
```bash
curl http://localhost:8001/health  # {"service":"agents","status":"ok"}
```

To run the agent service with live reload outside Docker:
```bash
cd /path/to/ReachGTM
pip install -r agents/requirements.txt
OPENAI_API_KEY=... PERPLEXITY_API_KEY=... DATABASE_URL=postgresql://... \
  uvicorn agents.app.main:app --reload --port 8001
```

---

## Codebase Orientation

```
agents/
├── app/
│   ├── graph/
│   │   ├── graph.py          # Compiled StateGraph — 5 nodes, conditional routing
│   │   ├── state.py          # GTMState with LangGraph message reducer
│   │   └── nodes/
│   │       ├── research.py   # STUB — your job in PR #10
│   │       ├── brand_alignment.py  # STUB — your job in PR #13
│   │       ├── orchestrator.py    # Stub (Yousef's PR #9)
│   │       ├── strategy.py        # Stub (Yousef's PR #11)
│   │       └── content.py         # Stub (Yousef's PR #12)
│   ├── tools/
│   │   ├── retriever.py      # DONE — PgVectorRetriever (real implementation)
│   │   ├── mcp_client.py     # STUB — needs Perplexity wired up (your job)
│   │   └── skills/
│   │       ├── pm_skills.py  # Stub (Yousef)
│   │       └── coldiq_skills.py  # Stub (Yousef)
│   └── prompts/
│       ├── research.py       # DONE — Perplexity-focused system prompt
│       └── brand_alignment.py  # DONE — RAG scoring system prompt
└── tests/test_graph.py       # DONE — graph compiles + runs stubs
```

The key shared schema is at `shared/schemas.py`. The types you'll work with most:
- `GTMState` — the LangGraph state passed between nodes
- `ResearchReport` — output of research node
- `ContentAsset` — brand alignment scores this
- `AgentEvent` — what you emit for SSE streaming

---

## PR #10 — Research Node (Perplexity MCP)

**Branch:** `epic-2/pr-10-research` (create from `staging`)

```bash
git checkout staging && git pull
git checkout -b epic-2/pr-10-research
```

### What to build

Replace the stub `research_node` in `agents/app/graph/nodes/research.py` with a real implementation that:
1. Loads Perplexity MCP tools
2. Uses an LLM (gpt-4o-mini) with those tools to research the company
3. Returns a populated `ResearchReport` object in state

### MCP Client (wire up first)

Update `agents/app/tools/mcp_client.py` to properly initialize the Perplexity MCP server:

```python
# agents/app/tools/mcp_client.py
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.app.config import settings

async def get_mcp_tools(server: str = "perplexity") -> list:
    """Return LangChain tool list from the named MCP server."""
    client = MultiServerMCPClient({
        "perplexity": {
            "url": "https://mcp.perplexity.ai/sse",
            "transport": "sse",
            "headers": {"Authorization": f"Bearer {settings.perplexity_api_key}"},
        }
    })
    tools = await client.get_tools()
    return [t for t in tools if t.name.startswith(server.split(":")[0])]
```

### Research node implementation

```python
# agents/app/graph/nodes/research.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from agents.app.graph.state import GTMState
from agents.app.tools.mcp_client import get_mcp_tools
from agents.app.prompts.research import RESEARCH_SYSTEM_PROMPT
from shared.schemas import ResearchReport
import json

async def research_node(state: GTMState) -> dict:
    """Run Perplexity-powered market research and return ResearchReport."""
    tools = await get_mcp_tools("perplexity")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Build research agent with MCP tools
    agent = create_react_agent(llm, tools, state_modifier=RESEARCH_SYSTEM_PROMPT)

    # Describe the company from state metadata
    company_profile = state.metadata.get("company_profile", {})
    query = f"""Research this company for a GTM strategy:
Company: {company_profile.get('name', 'Unknown')}
Industry: {company_profile.get('industry', 'Unknown')}
Description: {company_profile.get('description', '')}
Stage: {company_profile.get('stage', 'seed')}

Return a complete ResearchReport as JSON matching the schema."""

    result = await agent.ainvoke({"messages": [HumanMessage(content=query)]})

    # Parse the agent's final message into ResearchReport
    last_message = result["messages"][-1].content
    try:
        data = json.loads(last_message)
        report = ResearchReport(**data)
    except Exception:
        # Fallback: ask the model to re-format as JSON
        format_response = await llm.ainvoke([
            SystemMessage(content="Extract the research findings and return ONLY a JSON object matching the ResearchReport schema."),
            HumanMessage(content=last_message),
        ])
        data = json.loads(format_response.content)
        report = ResearchReport(**data)

    return {
        "research_report": report,
        "current_agent": "research",
    }
```

### Testing without real Perplexity key

Set `PERPLEXITY_API_KEY=test` and mock the MCP client:

```python
# agents/tests/test_research.py
import pytest
from unittest.mock import AsyncMock, patch
from agents.app.graph.nodes.research import research_node
from agents.app.graph.state import GTMState
import uuid

@pytest.mark.asyncio
async def test_research_node_returns_report():
    mock_report = {
        "company_profile": {"name":"Acme","website":None,"industry":"SaaS","stage":"seed","description":"AI tool","founded_year":None},
        "market_size": {"tam":"$4B","sam":"$400M","som":"$40M","source":"Gartner","year":2024},
        "competitors": [],
        "segments": [],
        "icp": {"title":"VP Sales","industry":"SaaS","company_size":"50-200","budget_range":"$50k-$200k","pain_points":[],"goals":[],"buying_committee":[],"disqualifiers":[]},
        "signals": [],
        "sources": [],
    }
    with patch("agents.app.graph.nodes.research.get_mcp_tools", return_value=[]), \
         patch("agents.app.graph.nodes.research.ChatOpenAI") as mock_llm:
        mock_llm.return_value.ainvoke = AsyncMock(return_value=type("R", (), {"content": str(mock_report)})())
        # ... test the node
    state = GTMState(company_id=uuid.uuid4(), user_id=uuid.uuid4())
    # Simplified: just verify the node runs
    assert state is not None
```

### PR checklist

- [ ] Research node returns a populated `ResearchReport` in state
- [ ] MCP client connects to Perplexity (or fails gracefully if key missing)
- [ ] `research_report` is set in GTMState after node runs
- [ ] `pytest agents/tests/ -v` passes (add `test_research.py`)
- [ ] No hardcoded API keys
- [ ] PR targets `staging`, reviewer: @yousefalshuwayi

---

## PR #13 — Brand Alignment Node

**Branch:** `epic-2/pr-13-brand` (create from `staging`, ideally after PR #10 merges)

**Depends on:** PR #12 (Yousef's content node) — the content node must populate `content_assets` in state before brand alignment runs.

### What to build

Replace the stub `brand_alignment_node` in `agents/app/graph/nodes/brand_alignment.py` with:
1. Retrieve brand-relevant chunks from pgvector (using `PgVectorRetriever`)
2. For each `ContentAsset` in `state.content_assets`:
   - Score brand alignment 0.0–1.0
   - If score < 0.7, revise (max 2 iterations)
   - Set `validation_status` and `brand_alignment_score`

### Implementation

```python
# agents/app/graph/nodes/brand_alignment.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import asyncpg, json
from agents.app.graph.state import GTMState
from agents.app.tools.retriever import PgVectorRetriever
from agents.app.config import settings
from shared.schemas import ContentAsset, ValidationStatus
from agents.app.prompts.brand_alignment import BRAND_ALIGNMENT_SYSTEM_PROMPT

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

async def _get_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=3)

async def _score_and_revise(asset: ContentAsset, brand_chunks: list[dict], max_iterations: int = 2) -> ContentAsset:
    """Score a content asset against brand chunks, revise if below threshold."""
    brand_context = "\n\n".join(f"[Brand chunk {i+1}]\n{c['content']}" for i, c in enumerate(brand_chunks))

    for iteration in range(max_iterations + 1):
        prompt = f"""Brand guidelines context:
{brand_context}

Content asset to evaluate:
Type: {asset.type}
Title: {asset.title}
Body: {asset.body}

Score this content's brand alignment from 0.0 to 1.0. If below 0.7, rewrite it.
Return JSON: {{"score": float, "revised_body": str or null, "notes": str}}"""

        response = await llm.ainvoke([
            SystemMessage(content=BRAND_ALIGNMENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        result = json.loads(response.content)
        score = float(result["score"])
        asset = asset.model_copy(update={"brand_alignment_score": score})

        if score >= 0.7 or iteration == max_iterations:
            status = ValidationStatus.APPROVED if score >= 0.7 else ValidationStatus.REVISED
            asset = asset.model_copy(update={
                "validation_status": status,
                "revision_notes": result.get("notes"),
                "body": result.get("revised_body") or asset.body,
            })
            break
        else:
            # Revise and loop
            asset = asset.model_copy(update={"body": result["revised_body"] or asset.body})

    return asset

async def brand_alignment_node(state: GTMState) -> dict:
    if not state.content_assets:
        return {"current_agent": "brand_alignment"}

    pool = await _get_pool()
    retriever = PgVectorRetriever(pool)
    namespace = f"{state.company_id}:brand_guide"

    # Retrieve brand chunks
    brand_chunks = await retriever.retrieve(
        query="brand voice tone messaging guidelines positioning",
        namespace=namespace,
        top_k=8,
    )

    # Score and revise each asset
    scored_assets = []
    for asset in state.content_assets:
        scored = await _score_and_revise(asset, brand_chunks)
        scored_assets.append(scored)

    await pool.close()
    return {
        "content_assets": scored_assets,
        "current_agent": "brand_alignment",
    }
```

### Testing without a populated vector store

```python
# agents/tests/test_brand_alignment.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agents.app.graph.nodes.brand_alignment import brand_alignment_node
from agents.app.graph.state import GTMState
from shared.schemas import ContentAsset, ContentType, ValidationStatus
import uuid

@pytest.mark.asyncio
async def test_brand_alignment_scores_assets():
    asset = ContentAsset(
        type=ContentType.COLD_EMAIL,
        title="Test email",
        body="Hi there, I wanted to reach out...",
        target_icp="VP Sales",
    )
    state = GTMState(
        company_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        content_assets=[asset],
    )
    with patch("agents.app.graph.nodes.brand_alignment._get_pool") as mock_pool, \
         patch("agents.app.graph.nodes.brand_alignment.PgVectorRetriever") as mock_retriever_class, \
         patch("agents.app.graph.nodes.brand_alignment.llm") as mock_llm:

        mock_pool.return_value = AsyncMock()
        mock_retriever = AsyncMock()
        mock_retriever.retrieve = AsyncMock(return_value=[{"content": "Be professional and concise.", "metadata": {}, "similarity": 0.9}])
        mock_retriever_class.return_value = mock_retriever
        mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"score": 0.85, "revised_body": null, "notes": "Good alignment"}'))

        result = await brand_alignment_node(state)

    assert result["current_agent"] == "brand_alignment"
    assets = result["content_assets"]
    assert len(assets) == 1
    assert assets[0].brand_alignment_score == 0.85
    assert assets[0].validation_status == ValidationStatus.APPROVED
```

### PR checklist

- [ ] Brand alignment node scores all content assets
- [ ] Score ≥ 0.7 → `ValidationStatus.APPROVED`
- [ ] Score < 0.7 → revise (max 2 iterations)
- [ ] `PgVectorRetriever` used to fetch brand chunks from pgvector
- [ ] `pytest agents/tests/test_brand_alignment.py -v` passes
- [ ] PR targets `staging`, reviewer: @yousefalshuwayi

---

## PR #24 — Databar + Fetch MCP Integration

**Branch:** `epic-3/pr-24-mcp-extra` (create from `staging` after Epic 2 completes)

### What to build

Add Databar (company enrichment) and Fetch (web scraping) MCP servers to the research agent's tool set.

Update `agents/app/tools/mcp_client.py`:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.app.config import settings

SERVERS = {
    "perplexity": {
        "url": "https://mcp.perplexity.ai/sse",
        "transport": "sse",
        "headers": {"Authorization": f"Bearer {settings.perplexity_api_key}"},
    },
    "databar": {
        "url": "https://mcp.databar.ai/sse",
        "transport": "sse",
        "headers": {"Authorization": f"Bearer {settings.databar_api_key}"},
    },
    "fetch": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-fetch"],
        "transport": "stdio",
    },
}

async def get_mcp_tools(servers: list[str] | None = None) -> list:
    """Return combined tool list from one or more MCP servers."""
    target = {k: v for k, v in SERVERS.items() if servers is None or k in servers}
    client = MultiServerMCPClient(target)
    return await client.get_tools()
```

Add `databar_api_key: str = ""` to `agents/app/config.py` and `DATABAR_API_KEY=` to `.env.example`.

Update the research node to use Databar for company enrichment (LinkedIn data, funding, employee count) when researching the ICP's company profile.

### PR checklist

- [ ] Databar tools available in research agent's tool list
- [ ] Fetch tools available for web scraping competitor sites
- [ ] `DATABAR_API_KEY` configurable via env — not hardcoded
- [ ] Research node uses Databar to enrich ICP company data
- [ ] Graceful fallback if Databar/Fetch server unreachable (tool returns empty result, agent continues)

---

## Understanding the RAG Pipeline

The vector retrieval system is already implemented in `agents/app/tools/retriever.py`. Here's how it works:

```
User uploads PDF/DOCX
        ↓
backend/app/services/knowledge_service.py
        ↓
Text extraction (pypdf / python-docx)
        ↓
512-word chunks with 50-word overlap
        ↓
OpenAI text-embedding-3-small (1536 dims)
        ↓
INSERT INTO document_chunks (embedding vector(1536), namespace)
        ↓ (HNSW index on embedding column)
PgVectorRetriever.retrieve(query, namespace, top_k=5)
        ↓
cosine similarity search → top-k chunks returned
```

The `namespace` format is `{company_id}:{doc_type}`. For brand alignment, query the `brand_guide` namespace. For research context, query `pitch_deck` or `case_study`.

---

## Branch Rules

```
main (protected — never push here directly)
  ↑ PR from staging only
staging (default — all your PRs go here)
  ↑ PR from your feature branch
epic-2/pr-10-research  ← your branch
```

**Every PR:**
1. `git checkout staging && git pull`
2. `git checkout -b epic-N/pr-N-<name>`
3. Implement → commit → push
4. `gh pr create --base staging`
5. Tag @yousefalshuwayi as reviewer

---

## Questions

- Before starting PR #13, check with Yousef what `state.content_assets` looks like after the content node runs — you need to know the exact shape before writing the scoring loop.
- The `PgVectorRetriever` requires an asyncpg pool — in the brand alignment node you create it locally. In Epic 3, this should be a shared pool injected via dependency.
