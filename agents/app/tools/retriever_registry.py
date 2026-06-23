"""Process-global retriever registry.

The graph compiles at import time and its nodes are plain `(state) -> state`
functions, so they can't receive a retriever as a constructor arg. The agents
service lifespan builds one `PgVectorRetriever` (backed by an asyncpg pool) and
registers it here; nodes look it up lazily at call time.
"""
from __future__ import annotations

from typing import Optional

from agents.app.tools.retriever import Retriever

_retriever: Optional[Retriever] = None


def set_retriever(retriever: Optional[Retriever]) -> None:
    global _retriever
    _retriever = retriever


def get_retriever() -> Optional[Retriever]:
    return _retriever
