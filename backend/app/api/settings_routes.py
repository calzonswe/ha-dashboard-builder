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


@router.post("/settings/reload")
def reload_settings(db: Session = Depends(get_db)):
    """Reload settings from database and update runtime configuration.

    POST /api/v1/settings/reload -> 200 { "message": "Settings reloaded" }
    """
    from app.services.llm_service import set_llm_service, LLMService

    # Read all settings from DB
    db_settings = db.query(Setting).all()
    settings_dict = {s.key: s.value for s in db_settings}

    # Update LLM service if provider/model changed
    llm_provider = settings_dict.get("llm_provider", "ollama")
    llm_model = settings_dict.get("llm_model", "llama3.2")
    llm_base_url = settings_dict.get(
        "llm_base_url",
        (
            "http://localhost:11434"
            if llm_provider == "ollama"
            else "http://localhost:1234/v1"
        ),
    )

    try:
        new_llm = LLMService(
            provider=llm_provider,
            model=llm_model,
            base_url=llm_base_url,
        )
        set_llm_service(new_llm)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reload LLM settings: {e}"
        )

    return {"message": "Settings reloaded successfully"}
