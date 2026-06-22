from __future__ import annotations

import httpx
from fastapi import APIRouter, Header, HTTPException, status

from app.config import settings
from app.middleware.ip_block import list_blocks, unblock, unblock_all

router = APIRouter(prefix="/gw/admin")


async def _require_admin(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing authorization header")
    token = authorization[7:]
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.auth_service_url}/validate",
                headers={"Authorization": f"Bearer {token}"},
            )
        if resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")
        data = resp.json()
        if "admin" not in data.get("roles", []):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required")
        return data
    except httpx.RequestError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="auth service unavailable") from exc


@router.get("/ip-blocks")
async def list_ip_blocks(authorization: str | None = Header(default=None)):
    await _require_admin(authorization)
    blocks = list_blocks()
    return {"blocked": blocks, "count": len(blocks)}


@router.delete("/ip-blocks", status_code=200)
async def flush_all_ip_blocks(authorization: str | None = Header(default=None)):
    await _require_admin(authorization)
    count = unblock_all()
    return {"flushed": count}


@router.delete("/ip-blocks/{ip}", status_code=200)
async def unblock_ip(ip: str, authorization: str | None = Header(default=None)):
    await _require_admin(authorization)
    if not unblock(ip):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{ip} is not currently blocked")
    return {"unblocked": ip}
