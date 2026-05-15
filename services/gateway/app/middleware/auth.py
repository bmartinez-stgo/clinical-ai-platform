import httpx
from fastapi import HTTPException, status
from fastapi.requests import Request

from app.config import settings


EXEMPT_PATHS = {"/health", "/ready", "/metrics", "/api/v1/status", "/"}


async def validate_token(request: Request) -> str:
    if not settings.token_validation_enabled:
        return None

    path = request.url.path
    if path in EXEMPT_PATHS:
        return None

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="missing authorization header")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="invalid authorization header")

    token = auth_header[7:]

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.auth_service_url}/validate",
                headers={"Authorization": f"Bearer {token}"}
            )

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="invalid token")

        return token
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="auth service unavailable")
