from enum import StrEnum

from pydantic_settings import BaseSettings


class AlgorithmType(StrEnum):
    """Supported rate limiting algorithms."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW_LOG = "sliding_window_log"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "API Rate Limiter"
    app_version: str = "1.0.0"
    debug: bool = False

    # Redis
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0

    # Rate Limiting
    rate_limit_algorithm: AlgorithmType = AlgorithmType.TOKEN_BUCKET
    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
