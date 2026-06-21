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
    name = "hubspot_create_sequence"

    def __init__(self):
        self.args = None

    async def ainvoke(self, args):
        self.args = args
        return {"ok": True}


class TestHubSpotSync:
    def test_sequence_payload_maps_content_asset(self):
        asset = _asset()
        payload = hubspot_sync._sequence_payload(asset)

        assert payload["sequence_name"] == "Test Email"
        assert payload["steps"][0]["type"] == "cold_email"
        assert payload["steps"][0]["subject"] == "Test Email"
        assert payload["steps"][0]["body"] == "Hello world"
        assert payload["metadata"]["content_asset_id"] == str(asset.id)
        assert payload["metadata"]["target_icp"] == "VP Sales"

    @pytest.mark.asyncio
    async def test_no_hubspot_returns_false(self, monkeypatch):
        async def _none(server):
            return []

        monkeypatch.setattr(hubspot_sync, "get_mcp_tools", _none)

        assert await hubspot_sync.sync_content_to_hubspot_sequence(_asset()) is False

    @pytest.mark.asyncio
    async def test_sync_sequence_returns_true_and_sends_payload(self, monkeypatch):
        tool = _Tool()

        async def _tools(server):
            assert server == "hubspot"
            return [tool]

        monkeypatch.setattr(hubspot_sync, "get_mcp_tools", _tools)

        assert await hubspot_sync.sync_content_to_hubspot_sequence(_asset()) is True
        assert tool.args["sequence_name"] == "Test Email"
        assert tool.args["steps"][0]["body"] == "Hello world"

    @pytest.mark.asyncio
    async def test_tool_error_returns_false(self, monkeypatch):
        class _BadTool:
            name = "hubspot_create_sequence"

            async def ainvoke(self, args):
                raise RuntimeError("boom")

        async def _tools(server):
            return [_BadTool()]

        monkeypatch.setattr(hubspot_sync, "get_mcp_tools", _tools)

        assert await hubspot_sync.sync_content_to_hubspot_sequence(_asset()) is False