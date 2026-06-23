from __future__ import annotations

from typing import Any

from shared.schemas import ContentAsset


async def get_mcp_tools(server: str) -> list:
    from agents.app.tools.mcp_client import get_mcp_tools as _get_mcp_tools

    return await _get_mcp_tools(server)


def _campaign_payload(asset: ContentAsset) -> dict[str, Any]:
    return {
        "campaign_name": asset.title,
        "content": {
            "type": asset.type.value,
            "title": asset.title,
            "body": asset.body,
        },
        "metadata": {
            "content_asset_id": str(asset.id),
            "target_icp": asset.target_icp,
            "validation_status": asset.validation_status.value,
            "brand_alignment_score": asset.brand_alignment_score,
        },
    }


async def sync_content_to_salesforce(asset: ContentAsset) -> bool:
    try:
        tools = await get_mcp_tools("salesforce")
        if not tools:
            return False

        tool = tools[0]
        await tool.ainvoke(_campaign_payload(asset))

        return True

    except Exception:
        return False