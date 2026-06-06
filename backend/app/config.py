from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str
    database_url: str
    redis_url: str
    langsmith_api_key: str = ""
    langsmith_project: str = "reachgtm"
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    s3_bucket_name: str = ""
    agents_url: str = "http://agents:8001"
    environment: str = "development"

settings = Settings()
