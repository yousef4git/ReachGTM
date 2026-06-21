from __future__ import annotations

from typing import Any

from shared.schemas import ContentAsset


async def get_mcp_tools(server: str) -> list:
    from agents.app.tools.mcp_client import get_mcp_tools as _get_mcp_tools

    return await _get_mcp_tools(server)


def _sequence_payload(asset: ContentAsset) -> dict[str, Any]:
    """Convert a ContentAsset into the payload HubSpot sequence tools expect."""
    return {
        "sequence_name": asset.title,
        "steps": [
            {
                "type": asset.type.value,
                "subject": asset.title,
                "body": asset.body,
            }
        ],
        "metadata": {
            "content_asset_id": str(asset.id),
            "target_icp": asset.target_icp,
            "validation_status": asset.validation_status.value,
            "brand_alignment_score": asset.brand_alignment_score,
        },
    }


async def sync_content_to_hubspot_sequence(asset: ContentAsset) -> bool:
    """Sync a generated ContentAsset to a HubSpot sequence via MCP.

    Graceful:
    - Returns False when HubSpot is unavailable.
    - Never raises.
    """
    try:
        tools = await get_mcp_tools("hubspot")
        if not tools:
            return False

        tool = next((t for t in tools if "sequence" in t.name.lower()), tools[0])
        await tool.ainvoke(_sequence_payload(asset))

        return True

    except Exception:
        return False


async def sync_content_to_hubspot(asset: ContentAsset) -> bool:
    """Backward-compatible alias for HubSpot sequence sync."""
    return await sync_content_to_hubspot_sequence(asset)