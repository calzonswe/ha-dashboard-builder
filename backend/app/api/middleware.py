"""JWT authentication middleware for protecting API routes."""

import os
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

# ─── Configuration ──────────────────────────────────────────────────

ALGORITHM = "HS256"
_jwt_secret = os.environ.get("JWT_SECRET", "dev-secret-change-in-production")

security = HTTPBearer(auto_error=False)


class AuthRequired(HTTPException):
    """Raised when authentication is required but not provided."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


# ─── Public routes (no auth needed) ────────────────────────────────

PUBLIC_ROUTES = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/verify-token",
    "/",
    "/health",
    "/docs",
    "/openapi.json",
}


def is_public_route(path: str) -> bool:
    """Check if a route path should bypass authentication."""
    # Exact match or prefix match for auth routes
    if path in PUBLIC_ROUTES:
        return True
    if path.startswith("/docs") or path.startswith("/openapi"):
        return True
    return False


# ─── Dependency ─────────────────────────────────────────────────────

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """FastAPI dependency that extracts and validates JWT from Bearer token.

    Returns the username (subject) if valid, otherwise raises 401.
    Public routes bypass authentication entirely.
    """
    path = request.url.path

    # Skip auth for public routes
    if is_public_route(path):
        return None

    # Require Authorization header
    if credentials is None:
        raise AuthRequired("Missing authorization header")

    token = credentials.credentials

    try:
        payload = jwt.decode(token, _jwt_secret, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no subject",
            )
        return username
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
