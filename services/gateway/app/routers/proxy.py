from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

logger = logging.getLogger(__name__)

from app.config import settings
from app.core.proxy_config import load_proxy_config, match_route, strip_prefix
from app.middleware.auth import check_rbac, validate_token
from app.middleware.ip_block import check_ip_block, get_client_ip, record_score
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
    "/documents": 26_214_400,   # 25 MB — PDF uploads
    "/stt":       104_857_600,  # 100 MB — audio uploads (30 min WAV worst case ~55 MB)
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
    ip = get_client_ip(request, settings.ip_trusted_proxies)

    # 1. IP block — static + dynamic deny list
    check_ip_block(ip, blocklist_csv=settings.ip_blocklist, enabled=settings.ip_block_enabled)

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
        except HTTPException:
            raise

    # 5. Route matching
    route = match_route(path, load_proxy_config())
    if not route:
        if path in ("/", ""):
            return RedirectResponse(url="/webui", status_code=302)
        logger.warning("no route matched", extra={"path": path})
        if settings.ip_block_enabled:
            record_score(ip, settings.ip_score_404, settings.ip_score_window_seconds, settings.ip_score_threshold)
        return JSONResponse(status_code=404, content={"detail": "not found", "path": path})

    # 6. Per-user rate limit (post-auth, keyed by subject + prefix)
    if settings.rate_limit_enabled and token_data:
        check_rate_limit(
            user_key(token_data["subject"], route.prefix),
            _route_rpm(route.prefix),
        )

    # 7. RBAC — role enforcement per route
    if token_data:
        try:
            check_rbac(route.prefix, token_data)
        except HTTPException:
            if settings.ip_block_enabled:
                record_score(ip, settings.ip_score_403, settings.ip_score_window_seconds, settings.ip_score_threshold)
            raise

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
        logger.error(
            "upstream unreachable",
            extra={"upstream": route.upstream, "error": str(exc)},
        )
        service = route.prefix.lstrip("/")
        return JSONResponse(
            status_code=503,
            content={"detail": "service temporarily unavailable", "service": service},
        )

    if settings.ip_block_enabled and upstream_response.status_code == 400:
        record_score(ip, settings.ip_score_400, settings.ip_score_window_seconds, settings.ip_score_threshold)

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
