from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, Response

from app.core.config import get_settings
from app.core.security import decode_access_token

router = APIRouter()
settings = get_settings()

_UI = Path(__file__).parent.parent / "ui"


def _require_token(authorization: str | None) -> dict:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authorization header")
    return decode_access_token(
        parts[1],
        settings.auth_token_secret,
        settings.jwt_issuer,
        settings.jwt_audience,
    )


@router.get("/ui", include_in_schema=False)
@router.get("/ui/", include_in_schema=False)
@router.get("/ui/index.html", include_in_schema=False)
async def management_ui():
    return FileResponse(_UI / "index.html", media_type="text/html")


@router.get("/ui/api-docs.html", include_in_schema=False)
async def api_docs():
    return FileResponse(_UI / "api-docs.html", media_type="text/html")


@router.get("/ui/openapi.json", include_in_schema=False)
async def openapi_spec(authorization: str | None = Header(default=None)):
    _require_token(authorization)
    return FileResponse(_UI / "openapi.json", media_type="application/json")


@router.get("/ui/clinical_ai_client.py", include_in_schema=False)
async def sdk_download(authorization: str | None = Header(default=None)):
    _require_token(authorization)
    content = (_UI / "clinical_ai_client.py").read_bytes()
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=clinical_ai_client.py"},
    )
