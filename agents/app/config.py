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

    perplexity_api_key: str = ""

    databar_api_key: str = ""
    databar_mcp_url: str = ""

    fetch_mcp_enabled: bool = True

    attio_api_key: str = ""
    attio_mcp_url: str = ""

    salesforce_api_key: str = ""
    salesforce_mcp_url: str = ""

    environment: str = "development"


settings = Settings()