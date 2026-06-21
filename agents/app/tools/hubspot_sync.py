from __future__ import annotations

from shared.schemas import ContentAsset


async def get_mcp_tools(server: str) -> list:
    from agents.app.tools.mcp_client import get_mcp_tools as _get_mcp_tools

    return await _get_mcp_tools(server)


async def sync_content_to_hubspot(asset: ContentAsset) -> bool:
    """Sync a generated content asset to HubSpot via MCP.

    Graceful:
    - Returns False when HubSpot is unavailable.
    - Never raises.
    """
    try:
        tools = await get_mcp_tools("hubspot")
        if not tools:
            return False

        tool = tools[0]

        await tool.ainvoke(
            {
                "title": asset.title,
                "body": asset.body,
                "type": str(asset.type),
                "target_icp": asset.target_icp,
            }
        )

        return True

    except Exception:
        return False