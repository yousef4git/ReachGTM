"""MCP client for the research agent.

Registers the MCP servers the research agent can use and returns their tools as
LangChain tools:

  - perplexity : web/market research (SSE, needs PERPLEXITY_API_KEY)
  - databar    : company/people data enrichment (HTTP, needs DATABAR_API_KEY + DATABAR_MCP_URL)
  - fetch      : fetch a URL's content (reference mcp-server-fetch, stdio, no key)
  - attio      : Attio CRM (enrich ICP, HTTP, needs ATTIO_API_KEY + ATTIO_MCP_URL)

A server is only registered when it is configured. `get_mcp_tools` never raises:
if a server is missing or unreachable it returns [], so the graph degrades
gracefully (the research node falls back to a stub report).
"""
from langchain_mcp_adapters.client import MultiServerMCPClient

from agents.app.config import settings


def _server_configs() -> dict:
    """Connection configs for the MCP servers that are currently configured."""
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
        # Reference fetch server, installed via agents/requirements.txt
        # (mcp-server-fetch) and run as a stdio subprocess.
        configs["fetch"] = {
            "command": "python",
            "args": ["-m", "mcp_server_fetch"],
            "transport": "stdio",
        }

    if settings.attio_api_key and settings.attio_mcp_url:
        configs["attio"] = {
            "url": settings.attio_mcp_url,
            "transport": "streamable_http",
            "headers": {"Authorization": f"Bearer {settings.attio_api_key}"},
        }

    return configs


async def get_mcp_tools(server: str = "perplexity") -> list:
    """Return LangChain tools from the named MCP server.

    Supported servers: 'perplexity', 'databar', 'fetch', 'attio'. Returns []
    when the server is not configured or cannot be reached, so callers degrade
    gracefully.
    """
    cfg = _server_configs().get(server)
    if cfg is None:
        return []
    try:
        client = MultiServerMCPClient({server: cfg})
        return await client.get_tools()
    except Exception:
        return []
