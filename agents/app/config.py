from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    database_url: str
    redis_url: str
    langsmith_api_key: str = ""
    langsmith_project: str = "reachgtm"
    perplexity_api_key: str = ""
    databar_api_key: str = ""
    databar_mcp_url: str = ""  # Databar MCP endpoint (from Databar docs)
    fetch_mcp_enabled: bool = True  # run the reference Fetch MCP server (stdio)
    attio_api_key: str = ""
    attio_mcp_url: str = ""  # Attio CRM MCP endpoint (from Attio docs)
    environment: str = "development"

settings = Settings()
