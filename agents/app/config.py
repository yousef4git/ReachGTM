from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    database_url: str
    redis_url: str
    langsmith_api_key: str = ""
    langsmith_project: str = "reachgtm"
    perplexity_api_key: str = ""
    environment: str = "development"

settings = Settings()
