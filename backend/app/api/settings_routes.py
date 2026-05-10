"""Settings API routes for persistent application configuration."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import SettingsModel, get_db

router = APIRouter()


# ─── Pydantic schemas ──────────────────────────────────────────────

class HAConnectionConfig(BaseModel):
    """Home Assistant connection settings."""
    ha_host: str = Field(default="localhost", description="HA hostname or IP")
    ha_port: int = Field(default=8123, ge=1, le=65535)
    ha_ssl: bool = Field(default=False)


class LLMConfig(BaseModel):
    """LLM provider configuration."""
    llm_provider: str = Field(default="ollama", pattern="^(ollama|lmstudio|none)$")
    llm_base_url: str = Field(default="http://localhost:11434")
    llm_model: str = Field(default="llama3.2", min_length=1)


class SettingsResponse(BaseModel):
    """Full application settings response."""
    app_name: Optional[str] = None
    ha_host: Optional[str] = None
    ha_port: Optional[int] = None
    ha_ssl: Optional[bool] = None
    llm_provider: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    onboarded: bool = False


class InitializeRequest(BaseModel):
    """Request to initialize settings during onboarding."""
    app_name: str = Field(default="HA Dashboard Builder")
    ha_host: str = "localhost"
    ha_port: int = 8123
    ha_ssl: bool = False
    ha_access_token: str = ""
    llm_provider: str = "ollama"
    llm_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2"


# ─── Routes ────────────────────────────────────────────────────────

@router.get("/settings", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    """Get current application settings (HA token masked)."""
    settings = db.query(SettingsModel).first()
    if not settings:
        return SettingsResponse(onboarded=False)

    return SettingsResponse(
        app_name=settings.app_name,
        ha_host=settings.ha_host,
        ha_port=settings.ha_port,
        ha_ssl=settings.ha_ssl,
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        onboarded=settings.onboarded,
    )


@router.put("/settings")
def update_settings(
    config: HAConnectionConfig | LLMConfig | dict,
    db: Session = Depends(get_db),
):
    """Update application settings.

    Accepts partial updates — only provided fields are changed.
    """
    settings = db.query(SettingsModel).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not initialized")

    update_data = config if isinstance(config, dict) else config.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    db.commit()
    db.refresh(settings)

    return SettingsResponse(
        app_name=settings.app_name,
        ha_host=settings.ha_host,
        ha_port=settings.ha_port,
        ha_ssl=settings.ha_ssl,
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        onboarded=settings.onboarded,
    )


@router.post("/settings/initialize", response_model=SettingsResponse)
def initialize_settings(
    request: InitializeRequest,
    db: Session = Depends(get_db),
):
    """Initialize application settings during onboarding.

    Creates or updates the app_settings record with all configuration values.
    The HA access token is encrypted before storage.
    """
    settings = db.query(SettingsModel).first()

    if settings and settings.onboarded:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Settings already initialized. Use PUT /api/settings to update.",
        )

    if settings is None:
        settings = SettingsModel()

    settings.app_name = request.app_name
    settings.ha_host = request.ha_host
    settings.ha_port = request.ha_port
    settings.ha_ssl = request.ha_ssl
    settings.llm_provider = request.llm_provider
    settings.llm_base_url = request.llm_base_url
    settings.llm_model = request.llm_model

    # Encrypt and store HA token
    if request.ha_access_token:
        from app.database import encrypt_token
        settings.ha_access_token_encrypted = encrypt_token(request.ha_access_token)

    db.commit()
    db.refresh(settings)

    return SettingsResponse(
        app_name=settings.app_name,
        ha_host=settings.ha_host,
        ha_port=settings.ha_port,
        ha_ssl=settings.ha_ssl,
        llm_provider=settings.llm_provider,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        onboarded=settings.onboarded,
    )


@router.get("/settings/onboarding-status")
def get_onboarding_status(db: Session = Depends(get_db)):
    """Check if onboarding has been completed."""
    settings = db.query(SettingsModel).first()
    return {"onboarded": bool(settings and settings.onboarded)}
