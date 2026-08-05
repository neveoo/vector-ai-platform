"""
Central application configuration.

FastAPI convention: settings are loaded once via pydantic-settings and
imported wherever needed, rather than reading os.environ scattered
throughout the codebase. This is the Python equivalent of a config.php
constants file, but validated and type-checked at startup.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "Vector"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+psycopg://neveo:neveo@localhost:5432/neveo"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Auth
    jwt_secret_key: str = "change-me-in-.env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # Object storage (S3-compatible)
    s3_bucket: str = "neveo-documents"
    s3_endpoint_url: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"

    # AI providers
    anthropic_api_key: str | None = None
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"  # local, free, no API cost
    embedding_dimensions: int = 384  # must match embedding_model_name's output size
    chat_model: str = "claude-sonnet-4-6"

    # RAG tuning
    chunk_size_tokens: int = 400
    chunk_overlap_tokens: int = 60
    retrieval_top_k: int = 8


@lru_cache
def get_settings() -> Settings:
    """
    Cached so we don't re-parse the environment on every request.
    Import this function (not a module-level Settings() instance) so
    tests can override it easily.
    """
    return Settings()
