"""Database setup and SQLAlchemy models."""

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Database engine (SQLite)
engine = create_engine("sqlite:///./ha_dashboard.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
Base = declarative_base()


class Page(Base):
    """A dashboard page in the visual builder."""

    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Living Room", "Kitchen"
    description = Column(String, default="", nullable=True)  # Optional dashboard description
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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


class Entity(Base):
    """A Home Assistant entity discovered from the instance."""

    __tablename__ = "entities"

    id = Column(String, primary_key=True)  # HA entity ID (e.g., sensor.temperature)
    name = Column(String, default="")
    state = Column(String, default="")
    attributes = Column(JSON, default=dict)  # Entity attributes as JSON
    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
