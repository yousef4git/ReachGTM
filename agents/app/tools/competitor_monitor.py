"""Competitor monitoring — weekly Perplexity refresh (Epic 4 — Phase 2).

Periodically refreshes competitor signals (funding, hiring, launches, leadership
changes) via the Perplexity MCP tool. Designed to be triggered on a weekly
cadence (e.g. a Railway cron hitting POST /monitor/competitors); the cadence
gate (`is_refresh_due`) lets the caller pass the last-run timestamp so a refresh
only runs when actually due.

Degrades gracefully: when Perplexity MCP isn't configured/reachable, the refresh
returns [] rather than raising, so a scheduled run never crashes.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from shared.schemas import Signal

REFRESH_INTERVAL_DAYS = 7


def is_refresh_due(
    last_run: Optional[datetime],
    now: Optional[datetime] = None,
    interval_days: int = REFRESH_INTERVAL_DAYS,
) -> bool:
    """True when a competitor refresh is due (never run, or >= interval old)."""
    if last_run is None:
        return True
    now = now or datetime.now(timezone.utc)
    if last_run.tzinfo is None:
        last_run = last_run.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now - last_run) >= timedelta(days=interval_days)


def _query_for(competitor: str) -> str:
    return (
        f"Recent news for {competitor} in the last 7 days: funding rounds, "
        f"product launches, key hires, leadership changes, or major announcements."
    )


async def refresh_competitor_signals(competitors: list[str]) -> list[Signal]:
    """Query Perplexity MCP for each competitor and return fresh Signals.

    Returns [] when Perplexity MCP is unavailable. A per-competitor failure is
    captured as an `error` Signal rather than aborting the whole refresh.
    """
    if not competitors:
        return []
    try:
        from agents.app.tools.mcp_client import get_mcp_tools
        tools = await get_mcp_tools("perplexity")
    except Exception:
        return []
    if not tools:
        return []

    tool = tools[0]
    signals: list[Signal] = []
    for name in competitors:
        try:
            result = await tool.ainvoke({"query": _query_for(name)})
            text = result if isinstance(result, str) else str(result)
            signals.append(
                Signal(
                    type="competitor_update",
                    description=f"{name}: {text}"[:1000],
                    relevance=f"Weekly monitoring signal for competitor {name}",
                )
            )
        except Exception as exc:
            signals.append(
                Signal(
                    type="error",
                    description=f"{name}: {type(exc).__name__}",
                    relevance="Competitor refresh failed for this competitor",
                )
            )
    return signals


async def monitor_competitors(
    competitors: list[str],
    last_run: Optional[datetime] = None,
    now: Optional[datetime] = None,
) -> dict:
    """Refresh competitor signals if due, else skip.

    Returns {"refreshed": bool, "signals": list[Signal]}. When not due, no MCP
    call is made.
    """
    if not is_refresh_due(last_run, now):
        return {"refreshed": False, "signals": []}
    signals = await refresh_competitor_signals(competitors)
    return {"refreshed": True, "signals": signals}
