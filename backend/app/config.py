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
    s3_endpoint_url: str = ""  # set for Cloudflare R2 / S3-compatible store; empty = AWS S3
    aws_region: str = "us-east-1"  # use "auto" for Cloudflare R2
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    agents_url: str = "http://agents:8001"
    environment: str = "development"

settings = Settings()
