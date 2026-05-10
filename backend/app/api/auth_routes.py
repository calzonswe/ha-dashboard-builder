"""Application authentication endpoints using JWT + bcrypt."""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db, SettingsModel

router = APIRouter()

# ─── Configuration ──────────────────────────────────────────────────

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Generate JWT secret from env or use a deterministic default for dev
_jwt_secret = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def _hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def _create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, _jwt_secret, algorithm=ALGORITHM)


# ─── Pydantic schemas ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


class UserResponse(BaseModel):
    username: str
    is_admin: bool = True


# ─── Helper: get/create admin user from DB ────────────────────────

def _get_or_create_admin(db: Session) -> Optional[SettingsModel]:
    """Retrieve the single app settings record (admin config)."""
    return db.query(SettingsModel).first()


# ─── Routes ────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new admin user (first-run only)."""
    existing = _get_or_create_admin(db)

    if existing and existing.onboarded:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Admin account already exists. Use /auth/login instead.",
        )

    # Check username uniqueness (simple check via settings record)
    if existing:
        # If there's a record but not onboarded yet, allow re-registration
        pass

    hashed = _hash_password(request.password)
    # Store password hash in the settings record as a special key
    from app.database import Setting
    setting = db.query(Setting).filter(Setting.key == f"auth_user_{request.username}").first()
    if not setting:
        setting = Setting(key=f"auth_user_{request.username}", value=hashed)
        db.add(setting)

    # Mark as onboarded and create/update settings record
    if existing is None:
        new_settings = SettingsModel(
            app_name="HA Dashboard Builder",
            ha_host="",
            ha_port=8123,
            ha_ssl=False,
            llm_provider="ollama",
            llm_base_url="http://localhost:11434",
            llm_model="llama3.2",
            onboarded=True,
        )
        db.add(new_settings)
    else:
        existing.onboarded = True

    db.commit()

    token_data = {"sub": request.username}
    access_token = _create_access_token(token_data)

    return TokenResponse(access_token=access_token, username=request.username)


@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive a JWT token."""
    # Find the settings record (admin user)
    existing = _get_or_create_admin(db)

    if not existing or not existing.onboarded:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No admin account configured. Register first.",
        )

    # Verify password against stored hash
    setting = db.query(Setting).filter(Setting.key == f"auth_user_{request.username}").first()
    if not setting or not _verify_password(request.password, setting.value):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token_data = {"sub": request.username}
    access_token = _create_access_token(token_data)

    return TokenResponse(access_token=access_token, username=request.username)


@router.get("/auth/me", response_model=UserResponse)
def get_current_user(
    token: str = None,
    db: Session = Depends(get_db),
):
    """Get current authenticated user info."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(_jwt_secret, token or "", algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return UserResponse(username=username)


@router.post("/auth/verify-token", response_model=UserResponse)
def verify_token(token: str, db: Session = Depends(get_db)):
    """Verify a token and return user info (for frontend auth checks)."""
    try:
        payload = jwt.decode(_jwt_secret, token, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return UserResponse(username=username)
