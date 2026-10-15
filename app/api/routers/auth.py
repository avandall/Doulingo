"""Authentication & User Personalization Router.

Provides registration, login, profile management, BYOK API key storage,
and user-specific settings.
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Any

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.storage.db import (
    authenticate_user,
    create_user,
    get_user_by_id,
    get_user_by_username,
    get_user_settings,
    update_user_api_keys,
    update_user_mother_tongue,
    update_user_settings,
)

logger = logging.getLogger("duolingo_speak.api.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication & User Profile"])

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "doulingo-secret-session-auth-key-2026")


# =========================================================================
# Lightweight Token Encoding / Decoding (Zero External C-Dependencies)
# =========================================================================

def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding and padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: str, username: str, expires_in_days: int = 30) -> str:
    """Generate HMAC-SHA256 signed access token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "name": username,
        "username": username,
        "exp": int(time.time()) + (expires_in_days * 86400),
    }
    encoded_header = _b64encode(json.dumps(header).encode("utf-8"))
    encoded_payload = _b64encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    encoded_sig = _b64encode(sig)
    return f"{encoded_header}.{encoded_payload}.{encoded_sig}"


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify signed access token and return decoded payload if valid."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return None
        encoded_header, encoded_payload, encoded_sig = parts
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64decode(encoded_sig)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64decode(encoded_payload).decode("utf-8"))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None


def get_current_user_from_header(authorization: str | None = Header(None)) -> dict[str, Any] | None:
    """Extract user payload from Authorization Bearer header, if provided."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    payload = verify_token(token)
    if not payload or not payload.get("sub"):
        return None
    user = get_user_by_id(payload["sub"])
    return user


# =========================================================================
# Request & Response Schemas
# =========================================================================

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    password: str = Field(..., min_length=4, max_length=128, description="Account password")
    mother_tongue: str = Field("en", description="User's native mother tongue code (e.g., vi, ja, ko, es)")
    custom_api_keys: dict[str, str] = Field(default_factory=dict, description="Optional initial API keys")


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UpdateMotherTongueRequest(BaseModel):
    mother_tongue: str = Field(..., description="New mother tongue code (e.g., vi, ja, ko, es, fr)")


class UpdateKeysRequest(BaseModel):
    custom_api_keys: dict[str, str] = Field(..., description="Dictionary of API keys (groq, gemini, openai)")


class UserSettingsRequest(BaseModel):
    target_band: str = Field("B2", description="Target CEFR band level")
    speech_rate: float = Field(1.0, ge=0.5, le=2.0, description="TTS playback speed rate")
    theme: str = Field("dark", description="UI theme preference")


class VerifyKeyRequest(BaseModel):
    provider: str = Field(..., description="Provider name: groq, gemini, or openai")
    key: str = Field(..., description="API key to test")


# =========================================================================
# API Endpoints
# =========================================================================

@router.post("/register")
def register(req: RegisterRequest) -> dict[str, Any]:
    """Register a new user account."""
    clean_username = req.username.strip().lower()
    existing = get_user_by_username(clean_username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists. Please choose a different name.",
        )

    user = create_user(
        username=clean_username,
        password=req.password,
        mother_tongue=req.mother_tongue,
        custom_api_keys=req.custom_api_keys,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not create user account. Username may already exist.",
        )
    token = create_token(user["id"], user["username"])
    return {
        "token": token,
        "user": user,
    }


@router.post("/login")
def login(req: LoginRequest) -> dict[str, Any]:
    """Authenticate existing user credentials."""
    user = authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_token(user["id"], user["username"])
    return {
        "token": token,
        "user": user,
    }


@router.get("/me")
def get_me(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Get profile of current authenticated user."""
    user = get_current_user_from_header(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required or token expired.",
        )
    return user


@router.put("/mother_tongue")
def update_mother_tongue(req: UpdateMotherTongueRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    """Update native language for the authenticated user."""
    user = get_current_user_from_header(authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    success = update_user_mother_tongue(user["id"], req.mother_tongue)
    return {"success": success, "mother_tongue": req.mother_tongue}


@router.put("/keys")
def update_keys(req: UpdateKeysRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    """Save personalized BYOK API keys for the authenticated user."""
    user = get_current_user_from_header(authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    # Sanitize keys: strip whitespace, remove empty entries
    clean_keys = {k.lower(): v.strip() for k, v in req.custom_api_keys.items() if v and v.strip()}
    success = update_user_api_keys(user["id"], clean_keys)
    return {"success": success, "custom_api_keys": clean_keys}


@router.get("/settings")
def get_settings(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Retrieve personal settings for the authenticated user."""
    user = get_current_user_from_header(authorization)
    if not user:
        return {"user_id": "guest", "target_band": "B2", "speech_rate": 1.0, "theme": "dark"}
    return get_user_settings(user["id"])


@router.put("/settings")
def update_settings(req: UserSettingsRequest, authorization: str | None = Header(None)) -> dict[str, Any]:
    """Save personalized user settings."""
    user = get_current_user_from_header(authorization)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    updated = update_user_settings(
        user["id"],
        {
            "target_band": req.target_band,
            "speech_rate": req.speech_rate,
            "theme": req.theme,
        },
    )
    return updated


@router.post("/verify_key")
def verify_api_key(req: VerifyKeyRequest) -> dict[str, Any]:
    """Quick validation ping for a user-provided API key."""
    provider = req.provider.strip().lower()
    key = req.key.strip()
    if not key:
        return {"valid": False, "error": "Key is empty"}

    try:
        import requests
        if provider == "groq":
            res = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=5,
            )
            return {"valid": res.status_code == 200, "status_code": res.status_code}
        elif provider == "gemini":
            res = requests.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
                timeout=5,
            )
            return {"valid": res.status_code == 200, "status_code": res.status_code}
        elif provider == "openai":
            res = requests.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=5,
            )
            return {"valid": res.status_code == 200, "status_code": res.status_code}
        else:
            return {"valid": False, "error": f"Unknown provider: {provider}"}
    except Exception as e:
        return {"valid": False, "error": str(e)}
