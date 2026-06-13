from __future__ import annotations

import time

import httpx
from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.ip_block import _dynamic_blocked, _dynamic_lock, _failure_lock, _failure_windows

router = APIRouter(prefix="/admin")


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
    now = time.time()
    with _dynamic_lock:
        blocks = [
            {
                "ip": ip,
                "unblocks_at": int(unblock_at),
                "seconds_remaining": max(0, int(unblock_at - now)),
            }
            for ip, unblock_at in _dynamic_blocked.items()
            if unblock_at > now
        ]
    return {"blocked": blocks, "count": len(blocks)}


@router.delete("/ip-blocks", status_code=200)
async def flush_all_ip_blocks(authorization: str | None = Header(default=None)):
    await _require_admin(authorization)
    with _dynamic_lock:
        count = len(_dynamic_blocked)
        _dynamic_blocked.clear()
    with _failure_lock:
        _failure_windows.clear()
    return {"flushed": count}


@router.delete("/ip-blocks/{ip}", status_code=200)
async def unblock_ip(ip: str, authorization: str | None = Header(default=None)):
    await _require_admin(authorization)
    with _dynamic_lock:
        if ip not in _dynamic_blocked:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{ip} is not currently blocked")
        del _dynamic_blocked[ip]
    with _failure_lock:
        _failure_windows.pop(ip, None)
    return {"unblocked": ip}
