import pytest

import agents.app.tools.salesforce_sync as salesforce_sync
from shared.schemas import ContentAsset, ContentType


def _asset() -> ContentAsset:
    return ContentAsset(
        type=ContentType.COLD_EMAIL,
        title="Test Campaign",
        body="Hello Salesforce",
        target_icp="VP Sales",
    )


class _Tool:
    def __init__(self):
        self.args = None

    async def ainvoke(self, args):
        self.args = args
        return {"ok": True}


class TestSalesforceSync:
    def test_campaign_payload_maps_content_asset(self):
        asset = _asset()
        payload = salesforce_sync._campaign_payload(asset)

        assert payload["campaign_name"] == "Test Campaign"
        assert payload["content"]["type"] == "cold_email"
        assert payload["content"]["title"] == "Test Campaign"
        assert payload["content"]["body"] == "Hello Salesforce"
        assert payload["metadata"]["content_asset_id"] == str(asset.id)
        assert payload["metadata"]["target_icp"] == "VP Sales"

    @pytest.mark.asyncio
    async def test_no_salesforce_returns_false(self, monkeypatch):
        async def _none(server):
            return []

        monkeypatch.setattr(salesforce_sync, "get_mcp_tools", _none)

        assert await salesforce_sync.sync_content_to_salesforce(_asset()) is False

    @pytest.mark.asyncio
    async def test_sync_returns_true_and_sends_payload(self, monkeypatch):
        tool = _Tool()

        async def _tools(server):
            assert server == "salesforce"
            return [tool]

        monkeypatch.setattr(salesforce_sync, "get_mcp_tools", _tools)

        assert await salesforce_sync.sync_content_to_salesforce(_asset()) is True
        assert tool.args["campaign_name"] == "Test Campaign"
        assert tool.args["content"]["body"] == "Hello Salesforce"

    @pytest.mark.asyncio
    async def test_tool_error_returns_false(self, monkeypatch):
        class _BadTool:
            async def ainvoke(self, args):
                raise RuntimeError("boom")

        async def _tools(server):
            return [_BadTool()]

        monkeypatch.setattr(salesforce_sync, "get_mcp_tools", _tools)

        assert await salesforce_sync.sync_content_to_salesforce(_asset()) is False