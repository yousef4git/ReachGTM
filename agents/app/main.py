import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    # TODO: Epic 2 PR #14 — invoke graph, stream events
    return {"status": "not_implemented"}
