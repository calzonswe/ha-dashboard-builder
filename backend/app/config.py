"""Application configuration settings."""

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    # Application settings
    APP_NAME: str = "HA Dashboard Builder"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./ha_dashboard.db"

    # Home Assistant connection
    HA_HOST: str = "localhost"
    HA_PORT: int = 8123
    HA_ACCESS_TOKEN: str = ""

    # WebSocket poll interval (seconds)
    WS_POLL_INTERVAL: float = 5.0

    # LLM settings (Ollama/LMStudio)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LMSTUDIO_BASE_URL: str = "http://localhost:1234"
    DEFAULT_LLM_MODEL: str = "llama3"

    # CORS settings (frontend origin)
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]


# Singleton instance
settings = Settings()
