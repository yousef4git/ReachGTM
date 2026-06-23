"""Live web search via the Serper.dev Google Search API.

Used to ground the research agent in real-time SERP data. The endpoint is a
single POST to https://google.serper.dev/search with an X-API-KEY header and a
JSON body ``{"q": <query>}``; the response carries an ``organic`` list of
{title, link, snippet} results (plus an optional knowledge graph).

Degrades gracefully: with no SERPER_API_KEY (or on any transport/HTTP error) it
returns an empty list so the research node falls back to model-only knowledge.
"""
from __future__ import annotations

import httpx

from agents.app.config import settings

_SERPER_URL = "https://google.serper.dev/search"


async def web_search(query: str, num: int = 6) -> list[dict]:
    """Return up to ``num`` organic results as {title, link, snippet} dicts.

    Never raises — returns [] when unconfigured or on failure.
    """
    if not settings.serper_api_key:
        return []

    headers = {
        "X-API-KEY": settings.serper_api_key,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(_SERPER_URL, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return []

    results: list[dict] = []

    kg = data.get("knowledgeGraph")
    if isinstance(kg, dict) and kg.get("description"):
        results.append(
            {
                "title": kg.get("title", "Knowledge Graph"),
                "link": kg.get("website") or kg.get("descriptionLink", ""),
                "snippet": kg.get("description", ""),
            }
        )

    for item in data.get("organic", [])[:num]:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
        )

    return results


def format_results(results: list[dict]) -> str:
    """Render search results as a compact, prompt-friendly block."""
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "").strip()
        snippet = r.get("snippet", "").strip()
        link = r.get("link", "").strip()
        lines.append(f"[{i}] {title}\n{snippet}\n{link}")
    return "\n\n".join(lines)
