import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.proxy_config import load_proxy_config, match_route, strip_prefix

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


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_request(full_path: str, request: Request):
    path = f"/{full_path}"
    route = match_route(path, load_proxy_config())

    if not route:
        if path in ("/", ""):
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/webui", status_code=302)
        return JSONResponse(
            status_code=404,
            content={
                "detail": "route not found in gateway proxy config",
                "path": path,
            },
        )

    upstream_path = strip_prefix(path, route.prefix)
    upstream_url = f"{route.upstream}{upstream_path}"

    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    body = await request.body()
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
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
            content={
                "detail": "upstream request failed",
                "upstream": route.upstream,
                "error": str(exc),
            },
        )

    response_headers = {
        key: value
        for key, value in upstream_response.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )
