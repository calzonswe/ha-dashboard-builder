"""Database setup and SQLAlchemy models."""

import os
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Database engine (SQLite)
engine = create_engine(
    "sqlite:///./ha_dashboard.db", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=True)
Base = declarative_base()


def _get_fernet_key() -> bytes:
    """Get or generate a Fernet encryption key from env var."""
    key_str = os.environ.get("SETTINGS_ENCRYPTION_KEY")
    if key_str:
        return key_str.encode()
    # Generate and store in env for this session (not persistent across restarts)
    return Fernet.generate_key()


def encrypt_token(token: str) -> Optional[str]:
    """Encrypt a Home Assistant access token using Fernet symmetric encryption."""
    if not token:
        return None
    fernet = Fernet(_get_fernet_key())
    encrypted = fernet.encrypt(token.encode("utf-8"))
    return encrypted.decode("utf-8")


def decrypt_token(encrypted_token: Optional[str]) -> Optional[str]:
    """Decrypt a Home Assistant access token."""
    if not encrypted_token:
        return None
    try:
        fernet = Fernet(_get_fernet_key())
        decrypted = fernet.decrypt(encrypted_token.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken:
        return None


class Page(Base):
    """A dashboard page in the visual builder."""

    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Living Room", "Kitchen"
    description = Column(
        String, default="", nullable=True
    )  # Optional dashboard description
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship to cards on this page
    cards = relationship("Card", back_populates="page", cascade="all, delete-orphan")


class Card(Base):
    """A card (widget) on a dashboard page."""

    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"))
    card_type = Column(String, nullable=False)  # e.g., "sensor", "graph", "button"
    title = Column(String, default="")
    entity_id = Column(String, default="")  # HA entity ID (e.g., sensor.temperature)
    config = Column(JSON, default=dict)  # Card configuration as JSON

    # Position and size on the canvas
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    width = Column(Integer, default=2)  # Grid units (HA uses 1-12 grid)
    height = Column(Integer, default=1)

    # Relationship to page
    page = relationship("Page", back_populates="cards")


class SettingsModel(Base):
    """Persistent application settings stored in the database.

    Replaces .env-based configuration with a GUI-driven first-run setup flow.
    Sensitive values (HA access token) are encrypted at rest using Fernet symmetric encryption.
    """

    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    app_name = Column(String, default="HA Dashboard Builder")
    ha_host = Column(String, default="localhost")
    ha_port = Column(Integer, default=8123)
    ha_ssl = Column(Boolean, default=False)
    ha_access_token_encrypted = Column(Text, nullable=True)  # Fernet-encrypted token
    llm_provider = Column(String, default="ollama")
    llm_base_url = Column(String, default="http://localhost:11434")
    llm_model = Column(String, default="llama3.2")
    onboarded = Column(Boolean, default=False)  # Whether onboarding wizard completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    @property
    def ha_access_token(self) -> Optional[str]:
        """Decrypt and return the HA access token."""
        return decrypt_token(self.ha_access_token_encrypted)

    @ha_access_token.setter
    def ha_access_token(self, value: str):
        """Encrypt and store the HA access token."""
        self.ha_access_token_encrypted = encrypt_token(value)


class Setting(Base):
    """Key-value store for application settings (legacy)."""

    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Initialize database tables
def init_db():
    """Create all database tables (idempotent — safe to call multiple times)."""
    Base.metadata.create_all(bind=engine)


# Dependency for FastAPI
def get_db():
    """FastAPI dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
