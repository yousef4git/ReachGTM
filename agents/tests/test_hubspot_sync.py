import pytest

import agents.app.tools.hubspot_sync as hubspot_sync
from shared.schemas import ContentAsset, ContentType


def _asset() -> ContentAsset:
    return ContentAsset(
        type=ContentType.COLD_EMAIL,
        title="Test Email",
        body="Hello world",
        target_icp="VP Sales",
    )


class _Tool:
    async def ainvoke(self, args):
        return {"ok": True}


class TestHubSpotSync:
    @pytest.mark.asyncio
    async def test_no_hubspot_returns_false(self, monkeypatch):
        async def _none(server):
            return []

        monkeypatch.setattr(hubspot_sync, "get_mcp_tools", _none)

        assert await hubspot_sync.sync_content_to_hubspot(_asset()) is False

    @pytest.mark.asyncio
    async def test_sync_returns_true(self, monkeypatch):
        async def _tools(server):
            assert server == "hubspot"
            return [_Tool()]

        monkeypatch.setattr(hubspot_sync, "get_mcp_tools", _tools)

        assert await hubspot_sync.sync_content_to_hubspot(_asset()) is True

    @pytest.mark.asyncio
    async def test_tool_error_returns_false(self, monkeypatch):
        class _BadTool:
            async def ainvoke(self, args):
                raise RuntimeError("boom")

        async def _tools(server):
            return [_BadTool()]

        monkeypatch.setattr(hubspot_sync, "get_mcp_tools", _tools)

        assert await hubspot_sync.sync_content_to_hubspot(_asset()) is False