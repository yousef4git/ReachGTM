"""Enrich an ICP from Attio CRM via MCP (Epic 4 — Phase 2).

Pulls real buying-committee roles, pain points, sizing, etc. from the company's
Attio CRM and merges them into the ICPProfile the agent is working with.

Graceful: when the Attio MCP server isn't configured/reachable, the original
ICP is returned unchanged, so this never breaks a graph run.
"""
from __future__ import annotations

from typing import Any

from shared.schemas import ICPProfile

# ICP list fields we merge (union, dedupe) and scalar fields we backfill.
_LIST_FIELDS = ("pain_points", "goals", "buying_committee", "disqualifiers")
_SCALAR_FIELDS = ("company_size", "budget_range")
_EMPTY_SCALARS = {"", "unknown", "n/a", "none"}


def _union(existing: list[str], incoming: Any) -> list[str]:
    """Append new string items, preserving order and dropping duplicates."""
    if not isinstance(incoming, list):
        return existing
    out = list(existing)
    seen = {x for x in existing}
    for item in incoming:
        if isinstance(item, str) and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _merge_icp(icp: ICPProfile, data: dict) -> ICPProfile:
    """Merge an Attio enrichment payload into the ICP (non-destructive)."""
    update: dict[str, Any] = {}

    for field in _LIST_FIELDS:
        if field in data:
            merged = _union(getattr(icp, field), data[field])
            if merged != getattr(icp, field):
                update[field] = merged

    for field in _SCALAR_FIELDS:
        incoming = data.get(field)
        current = getattr(icp, field)
        # Only backfill when we have a real incoming value and the current is empty/unknown.
        if isinstance(incoming, str) and incoming.strip() and current.strip().lower() in _EMPTY_SCALARS:
            update[field] = incoming

    return icp.model_copy(update=update) if update else icp


async def enrich_icp_from_attio(icp: ICPProfile) -> ICPProfile:
    """Return an ICP enriched with Attio CRM data, or the original on any miss.

    Never raises — Attio being unconfigured, unreachable, or returning an
    unexpected shape all yield the unchanged ICP.
    """
    try:
        from agents.app.tools.mcp_client import get_mcp_tools
        tools = await get_mcp_tools("attio")
        if not tools:
            return icp
        tool = next((t for t in tools if "enrich" in t.name.lower()), tools[0])
        result = await tool.ainvoke({"title": icp.title, "industry": icp.industry})
    except Exception:
        return icp

    if isinstance(result, dict):
        return _merge_icp(icp, result)
    return icp
