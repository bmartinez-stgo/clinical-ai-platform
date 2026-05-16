import json

import aiosqlite
from fastapi import APIRouter, Form, HTTPException, Request, status
from pydantic import BaseModel

from app.core.brute_force import is_locked_out, record_failure, record_success
from app.core.config import get_settings
from app.core.database import DB_PATH
from app.core.security import create_access_token, verify_password

router = APIRouter()
settings = get_settings()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/token", response_model=TokenResponse)
async def client_token(
    request: Request,
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")

    ip = request.client.host if request.client else "unknown"
    locked, retry_after = is_locked_out(ip)
    if locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many failed attempts",
            headers={"Retry-After": str(retry_after)},
        )

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT secret_hash, roles, enabled FROM clients WHERE client_id = ?",
            (client_id,),
        )
        row = await cur.fetchone()

    if not row or not row["enabled"] or not verify_password(client_secret, row["secret_hash"]):
        record_failure(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid client credentials")

    record_success(ip)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE clients SET last_used_at = datetime('now') WHERE client_id = ?",
            (client_id,),
        )
        await db.commit()

    roles = json.loads(row["roles"])
    ttl = settings.client_token_ttl_seconds
    token = create_access_token(
        subject=client_id,
        roles=roles,
        secret=settings.auth_token_secret,
        expiration_seconds=ttl,
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )
    return TokenResponse(access_token=token, expires_in=ttl)
