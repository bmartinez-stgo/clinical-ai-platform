from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings
from app.core.proxy_config import load_proxy_config, match_route, strip_prefix
from app.middleware.auth import check_rbac, validate_token
from app.middleware.ip_block import check_ip_block, record_failure
from app.middleware.rate_limit import check_rate_limit, ip_key, user_key

router = APIRouter()

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}

# Body size limits per route prefix (bytes)
_BODY_LIMITS: dict[str, int] = {
    "/documents": 26_214_400,  # 25 MB — PDF uploads
}
_DEFAULT_BODY_LIMIT = 1_048_576  # 1 MB


def _body_limit(path: str) -> int:
    for prefix, limit in _BODY_LIMITS.items():
        if path.startswith(prefix):
            return limit
    return _DEFAULT_BODY_LIMIT


def _route_rpm(prefix: str) -> int:
    mapping = {
        "/auth": settings.rate_limit_auth_rpm,
        "/documents": settings.rate_limit_documents_rpm,
        "/diagnostics": settings.rate_limit_diagnostics_rpm,
        "/clinical-chat": settings.rate_limit_clinical_chat_rpm,
        "/rag": settings.rate_limit_rag_rpm,
        "/portal": settings.rate_limit_portal_rpm,
    }
    return mapping.get(prefix, settings.rate_limit_default_rpm)


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_request(full_path: str, request: Request):
    path = f"/{full_path}"
    # Prefer X-Real-IP set by Nginx ingress over the pod-network IP of the proxy
    ip = request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")

    # 1. IP block — static + dynamic deny list
    check_ip_block(
        request,
        blocklist_csv=settings.ip_blocklist,
        enabled=settings.ip_block_enabled,
    )

    # 2. Content-Length pre-check (fast reject before reading body into memory)
    cl_header = request.headers.get("content-length")
    if cl_header:
        try:
            if int(cl_header) > _body_limit(path):
                return JSONResponse(status_code=413, content={"detail": "request body too large"})
        except ValueError:
            pass

    # 3. Pre-auth IP rate limit for auth-mutating endpoints
    if settings.rate_limit_enabled and path in ("/auth/login", "/auth/refresh"):
        check_rate_limit(ip_key(request, "auth-sensitive"), settings.rate_limit_auth_sensitive_rpm)
    if settings.rate_limit_enabled and path == "/auth/token":
        check_rate_limit(ip_key(request, "auth-token"), settings.rate_limit_token_rpm)

    # 4. Token validation — cached + circuit-broken
    token_data = None
    if path not in ("/", ""):
        try:
            token_data = await validate_token(request)
        except HTTPException as exc:
            if exc.status_code == 401 and settings.ip_block_enabled:
                record_failure(
                    ip,
                    window_seconds=settings.ip_auto_block_window_seconds,
                    threshold=settings.ip_auto_block_threshold,
                    block_duration=settings.ip_auto_block_duration_seconds,
                )
            raise

    # 5. Route matching
    route = match_route(path, load_proxy_config())
    if not route:
        if path in ("/", ""):
            return RedirectResponse(url="/webui", status_code=302)
        return JSONResponse(
            status_code=404,
            content={"detail": "route not found in gateway proxy config", "path": path},
        )

    # 6. Per-user rate limit (post-auth, keyed by subject + prefix)
    if settings.rate_limit_enabled and token_data:
        check_rate_limit(
            user_key(token_data["subject"], route.prefix),
            _route_rpm(route.prefix),
        )

    # 7. RBAC — role enforcement per route
    if token_data:
        check_rbac(route.prefix, token_data)

    # 8. Read body + enforce actual size (catches chunked transfer bypasses)
    body = await request.body()
    if len(body) > _body_limit(path):
        return JSONResponse(status_code=413, content={"detail": "request body too large"})

    # 9. Proxy to upstream
    upstream_path = strip_prefix(path, route.prefix)
    upstream_url = f"{route.upstream}{upstream_path}"
    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            upstream_response = await client.request(
                method=request.method,
                url=upstream_url,
                content=body,
                headers=headers,
            )
    except httpx.RequestError as exc:
        return JSONResponse(
            status_code=502,
            content={"detail": "upstream request failed", "upstream": route.upstream, "error": str(exc)},
        )

    response_headers = {
        k: v
        for k, v in upstream_response.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )
