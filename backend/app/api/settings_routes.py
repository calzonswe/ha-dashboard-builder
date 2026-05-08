"""Settings API routes for application configuration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db, Setting

router = APIRouter()


@router.get("/settings")
def get_all_settings(db: Session = Depends(get_db)):
    """Return all settings as key-value pairs.

    GET /api/v1/settings -> 200 { "settings": { "key": "value", ... } }
    """
    settings = db.query(Setting).all()
    return {"settings": {s.key: s.value for s in settings}}


@router.get("/settings/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    """Return a single setting by key.

    GET /api/v1/settings/llm_provider -> 200 { "key": "llm_provider", "value": "ollama" }
    """
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return {"key": setting.key, "value": setting.value}


@router.put("/settings/{key}")
def upsert_setting(key: str, value: str | None, db: Session = Depends(get_db)):
    """Create or update a setting.

    PUT /api/v1/settings/llm_provider -> 200 { "key": "llm_provider", "value": "ollama" }
    """
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        setting = Setting(key=key, value=value)
        db.add(setting)
    db.commit()
    db.refresh(setting)
    return {"key": setting.key, "value": setting.value}


@router.put("/settings")
def upsert_multiple_settings(
    settings: dict[str, str | None],
    db: Session = Depends(get_db),
):
    """Create or update multiple settings at once.

    PUT /api/v1/settings -> 200 { "settings": { "key": "value", ... } }
    """
    for key, value in settings.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            db.add(setting)
    db.commit()

    all_settings = db.query(Setting).all()
    return {"settings": {s.key: s.value for s in all_settings}}


@router.delete("/settings/{key}")
def delete_setting(key: str, db: Session = Depends(get_db)):
    """Delete a setting.

    DELETE /api/v1/settings/llm_provider -> 204 (no content)
    """
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    db.delete(setting)
    db.commit()
    return None
