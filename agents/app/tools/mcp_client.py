from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.app.config import settings

async def get_mcp_tools() -> list:
    # TODO: Epic 3 — add Databar, Fetch, Attio MCP servers
    client = MultiServerMCPClient({
        "perplexity": {
            "url": "https://mcp.perplexity.ai",
            "api_key": settings.perplexity_api_key,
        }
    })
    return await client.get_tools()
