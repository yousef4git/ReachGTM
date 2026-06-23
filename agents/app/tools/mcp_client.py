"""MCP client for the research agent."""
from langchain_mcp_adapters.client import MultiServerMCPClient

from agents.app.config import settings


def _server_configs() -> dict:
    configs: dict = {}

    if settings.perplexity_api_key:
        configs["perplexity"] = {
            "url": "https://mcp.perplexity.ai/sse",
            "transport": "sse",
            "headers": {"Authorization": f"Bearer {settings.perplexity_api_key}"},
        }

    if settings.databar_api_key and settings.databar_mcp_url:
        configs["databar"] = {
            "url": settings.databar_mcp_url,
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {settings.databar_api_key}"},
        }

    if settings.fetch_mcp_enabled:
        configs["fetch"] = {
            "command": "python",
            "args": ["-m", "mcp_server_fetch"],
            "transport": "stdio",
        }

    if settings.salesforce_api_key and settings.salesforce_mcp_url:
        configs["salesforce"] = {
            "url": settings.salesforce_mcp_url,
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {settings.salesforce_api_key}"
            },
        }

    return configs


async def get_mcp_tools(server: str = "perplexity") -> list:
    cfg = _server_configs().get(server)
    if cfg is None:
        return []

    try:
        client = MultiServerMCPClient({server: cfg})
        return await client.get_tools()
    except Exception:
        return []