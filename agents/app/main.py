import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agents.app.config import settings

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project

@asynccontextmanager
async def lifespan(app: FastAPI):
    from agents.app.graph.graph import graph  # noqa: F401 — validate graph compiles
    yield

app = FastAPI(title="ReachGTM Agents", version="0.1.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://backend:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"service": "agents", "status": "ok"}

@app.post("/run")
async def run(body: dict):
    """Run the GTM graph and stream AgentEvents as SSE.

    Body: {company_id?, user_id?, goal?, content_types?, count_per_type?}.
    The goal is driven via metadata (see agents.app.graph.stream).
    """
    from agents.app.graph.stream import build_initial_state, stream_graph_sse

    state = build_initial_state(
        company_id=body.get("company_id"),
        user_id=body.get("user_id"),
        goal=body.get("goal"),
        content_types=body.get("content_types"),
        count_per_type=body.get("count_per_type", 3),
    )
    return StreamingResponse(stream_graph_sse(state), media_type="text/event-stream")


@app.post("/monitor/competitors")
async def monitor_competitors_endpoint(body: dict):
    """Weekly competitor monitoring trigger (e.g. called by a scheduled cron).

    Body: {competitors: [str], last_run?: ISO-8601 datetime}. Refreshes signals
    via Perplexity MCP only when the weekly cadence is due.
    """
    from datetime import datetime
    from agents.app.tools.competitor_monitor import monitor_competitors

    last_run_raw = body.get("last_run")
    last_run = datetime.fromisoformat(last_run_raw) if last_run_raw else None

    result = await monitor_competitors(
        competitors=body.get("competitors", []),
        last_run=last_run,
    )
    return {
        "refreshed": result["refreshed"],
        "signals": [s.model_dump(mode="json") for s in result["signals"]],
    }
