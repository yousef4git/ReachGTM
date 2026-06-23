from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    openai_api_key: str
    database_url: str
    redis_url: str

    langsmith_api_key: str = ""
    langsmith_project: str = "reachgtm"

    # Model + sampling for LLM-generated marketing content. Temperature is high
    # (creative copy); kept in config so the model isn't hardcoded in node logic.
    content_model: str = "gpt-4o-mini"
    content_temperature: float = 0.7

    perplexity_api_key: str = ""

    # Serper.dev — Google Search API used to ground the research agent in live web
    # results. Empty = the research agent runs on model knowledge only.
    serper_api_key: str = ""

    databar_api_key: str = ""
    databar_mcp_url: str = ""

    fetch_mcp_enabled: bool = True

    salesforce_api_key: str = ""
    salesforce_mcp_url: str = ""

    environment: str = "development"


settings = Settings()