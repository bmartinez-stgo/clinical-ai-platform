import json
import secrets
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import aiosqlite
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.database import DB_PATH
from app.core.security import decode_access_token, hash_password

router = APIRouter(prefix="/admin/clients")
settings = get_settings()

_ALLOWED_ROLES = {"user", "admin"}


def require_admin(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authorization header")
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid authorization header")
    claims = decode_access_token(
        parts[1],
        settings.auth_token_secret,
        settings.jwt_issuer,
        settings.jwt_audience,
    )
    if "admin" not in claims.get("roles", []):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required")
    return claims


class ClientInfo(BaseModel):
    client_id: str
    name: str
    description: str
    roles: List[str]
    enabled: bool
    created_at: str
    last_used_at: Optional[str]


class CreateRequest(BaseModel):
    name: str
    description: str = ""
    roles: List[str] = ["user"]


class CreateResponse(BaseModel):
    client_id: str
    client_secret: str
    name: str
    roles: List[str]


class UpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    roles: Optional[List[str]] = None
    enabled: Optional[bool] = None


class RotateResponse(BaseModel):
    client_id: str
    client_secret: str


def _row_to_info(row) -> ClientInfo:
    return ClientInfo(
        client_id=row["client_id"],
        name=row["name"],
        description=row["description"],
        roles=json.loads(row["roles"]),
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
        last_used_at=row["last_used_at"],
    )


@router.get("", response_model=List[ClientInfo])
async def list_clients(_: dict = Depends(require_admin)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT client_id, name, description, roles, enabled, created_at, last_used_at "
            "FROM clients ORDER BY created_at DESC"
        )
        rows = await cur.fetchall()
    return [_row_to_info(r) for r in rows]


@router.post("", response_model=CreateResponse, status_code=201)
async def create_client(payload: CreateRequest, _: dict = Depends(require_admin)):
    invalid = [r for r in payload.roles if r not in _ALLOWED_ROLES]
    if invalid:
        raise HTTPException(status_code=400, detail=f"invalid roles: {invalid}")

    client_id = f"client-{uuid.uuid4().hex[:8]}"
    plain_secret = secrets.token_urlsafe(32)
    hashed = hash_password(plain_secret)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO clients (client_id, name, description, secret_hash, roles, enabled, created_at) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (client_id, payload.name, payload.description, hashed, json.dumps(payload.roles), now),
        )
        await db.commit()

    return CreateResponse(
        client_id=client_id,
        client_secret=plain_secret,
        name=payload.name,
        roles=payload.roles,
    )


@router.get("/{client_id}", response_model=ClientInfo)
async def get_client(client_id: str, _: dict = Depends(require_admin)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT client_id, name, description, roles, enabled, created_at, last_used_at "
            "FROM clients WHERE client_id = ?",
            (client_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="client not found")
    return _row_to_info(row)


@router.patch("/{client_id}", response_model=ClientInfo)
async def update_client(client_id: str, payload: UpdateRequest, _: dict = Depends(require_admin)):
    if payload.roles is not None:
        invalid = [r for r in payload.roles if r not in _ALLOWED_ROLES]
        if invalid:
            raise HTTPException(status_code=400, detail=f"invalid roles: {invalid}")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT client_id FROM clients WHERE client_id = ?", (client_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="client not found")

        fields: dict = {}
        if payload.name is not None:
            fields["name"] = payload.name
        if payload.description is not None:
            fields["description"] = payload.description
        if payload.roles is not None:
            fields["roles"] = json.dumps(payload.roles)
        if payload.enabled is not None:
            fields["enabled"] = 1 if payload.enabled else 0

        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            await db.execute(
                f"UPDATE clients SET {set_clause} WHERE client_id = ?",
                [*fields.values(), client_id],
            )
            await db.commit()

        cur = await db.execute(
            "SELECT client_id, name, description, roles, enabled, created_at, last_used_at "
            "FROM clients WHERE client_id = ?",
            (client_id,),
        )
        row = await cur.fetchone()
    return _row_to_info(row)


@router.delete("/{client_id}", status_code=204)
async def delete_client(client_id: str, _: dict = Depends(require_admin)):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM clients WHERE client_id = ?", (client_id,))
        await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="client not found")


@router.post("/{client_id}/rotate", response_model=RotateResponse)
async def rotate_secret(client_id: str, _: dict = Depends(require_admin)):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT client_id FROM clients WHERE client_id = ?", (client_id,))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="client not found")

        plain_secret = secrets.token_urlsafe(32)
        hashed = hash_password(plain_secret)
        await db.execute("UPDATE clients SET secret_hash = ? WHERE client_id = ?", (hashed, client_id))
        await db.commit()

    return RotateResponse(client_id=client_id, client_secret=plain_secret)
