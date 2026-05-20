from __future__ import annotations

import hashlib
import threading
import time
from enum import Enum
from typing import Optional

import httpx
from fastapi import HTTPException, Request

from app.config import settings


EXEMPT_PATHS = {"/health", "/ready", "/metrics", "/api/v1/status", "/", "/auth/login", "/auth/refresh", "/auth/token", "/portal", "/portal/"}
EXEMPT_PREFIXES = ("/auth/ui/",)

# ---------------------------------------------------------------------------
# Token validation cache
# ---------------------------------------------------------------------------

_cache: dict[str, tuple[dict, float]] = {}  # token_hash -> (data, expires_at)
_cache_lock = threading.Lock()
_CACHE_TTL = 30  # seconds


def _cache_get(token: str) -> Optional[dict]:
    key = hashlib.sha256(token.encode()).hexdigest()
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() < entry[1]:
            return entry[0]
        if entry:
            del _cache[key]
    return None


def _cache_set(token: str, data: dict) -> None:
    key = hashlib.sha256(token.encode()).hexdigest()
    token_exp = data.get("expires_at", 0)
    ttl = min(_CACHE_TTL, max(0, token_exp - int(time.time())))
    if ttl <= 0:
        return
    with _cache_lock:
        _cache[key] = (data, time.time() + ttl)


# ---------------------------------------------------------------------------
# Circuit breaker for auth service
# ---------------------------------------------------------------------------

class _CBState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


_cb_state = _CBState.CLOSED
_cb_failures = 0
_cb_open_until = 0.0
_cb_lock = threading.Lock()
_CB_THRESHOLD = 3
_CB_OPEN_SECONDS = 30


def _cb_allow() -> bool:
    global _cb_state, _cb_failures, _cb_open_until
    with _cb_lock:
        if _cb_state == _CBState.CLOSED:
            return True
        if _cb_state == _CBState.OPEN:
            if time.time() >= _cb_open_until:
                _cb_state = _CBState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN: allow one probe


def _cb_success() -> None:
    global _cb_state, _cb_failures
    with _cb_lock:
        _cb_state = _CBState.CLOSED
        _cb_failures = 0


def _cb_failure() -> None:
    global _cb_state, _cb_failures, _cb_open_until
    with _cb_lock:
        _cb_failures += 1
        if _cb_state == _CBState.HALF_OPEN or _cb_failures >= _CB_THRESHOLD:
            _cb_state = _CBState.OPEN
            _cb_open_until = time.time() + _CB_OPEN_SECONDS
            _cb_failures = 0


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------

_ROUTE_REQUIRED_ROLES: dict[str, set[str]] = {
    "/portal": {"admin"},
}
_DEFAULT_REQUIRED_ROLES: set[str] = {"user", "admin"}


def check_rbac(prefix: str, token_data: dict) -> None:
    required = _ROUTE_REQUIRED_ROLES.get(prefix, _DEFAULT_REQUIRED_ROLES)
    user_roles = set(token_data.get("roles", []))
    if not user_roles.intersection(required):
        raise HTTPException(status_code=403, detail="insufficient permissions")


# ---------------------------------------------------------------------------
# Token validation (cached + circuit-broken)
# ---------------------------------------------------------------------------

async def validate_token(request: Request) -> Optional[dict]:
    """Returns {subject, roles, expires_at} or None for exempt paths."""
    if not settings.token_validation_enabled:
        return None

    path = request.url.path
    if path in EXEMPT_PATHS or any(path.startswith(p) for p in EXEMPT_PREFIXES):
        return None

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing authorization header")

    token = auth_header[7:]

    cached = _cache_get(token)
    if cached:
        return cached

    if not _cb_allow():
        raise HTTPException(status_code=503, detail="auth service unavailable")

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.auth_service_url}/validate",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code >= 500:
            _cb_failure()
            raise HTTPException(status_code=503, detail="auth service unavailable")
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="invalid token")

        _cb_success()
        body = response.json()
        token_data: dict = {
            "subject": body.get("subject", ""),
            "roles": body.get("roles", []),
            "expires_at": body.get("expires_at", 0),
        }
        _cache_set(token, token_data)
        return token_data

    except httpx.RequestError:
        _cb_failure()
        raise HTTPException(status_code=502, detail="auth service unavailable")
