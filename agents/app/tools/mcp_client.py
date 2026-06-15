from langchain_mcp_adapters.client import MultiServerMCPClient
from agents.app.config import settings


async def get_mcp_tools(server: str = "perplexity") -> list:
    """Return LangChain tool list from the named MCP server."""

    client = MultiServerMCPClient(
        {
            "perplexity": {
                "url": "https://mcp.perplexity.ai/sse",
                "transport": "sse",
                "headers": {
                    "Authorization": f"Bearer {settings.perplexity_api_key}",
                },
            }
        }
    )

    tools = await client.get_tools()
    return [
        tool
        for tool in tools
        if tool.name.startswith(server.split(":")[0])
    ]