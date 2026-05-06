"""Configuration module for HA Integration API."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Home Assistant connection
    ha_url: str = "http://localhost:8123"
    ha_token: str = ""
    ha_timeout: float = 10.0
    ha_max_retries: int = 3
    ha_retry_delay: float = 1.0

    # Entity caching
    cache_ttl_seconds: int = 60
    cache_refresh_interval: int = 300  # 5 minutes default

    # WebSocket
    ws_ping_interval: float = 30.0
    ws_ping_timeout: float = 10.0

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_prefix = "HA_INTEGRATION_"
        case_sensitive = True


settings = Settings()
