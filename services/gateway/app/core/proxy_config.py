from dataclasses import dataclass
from pathlib import Path

import yaml

from app.config import settings


@dataclass(frozen=True)
class ProxyRoute:
    prefix: str
    upstream: str


def normalize_prefix(prefix: str) -> str:
    cleaned = prefix.strip()
    if not cleaned:
        return "/"

    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"

    cleaned = cleaned.rstrip("/")
    return cleaned or "/"


def load_proxy_config() -> list[ProxyRoute]:
    config_path = Path(settings.proxy_config_path)
    if not config_path.exists():
        return []

    payload = yaml.safe_load(config_path.read_text()) or {}
    routes = payload.get("routes", [])

    parsed_routes = [
        ProxyRoute(
            prefix=normalize_prefix(route["prefix"]),
            upstream=route["upstream"].rstrip("/"),
        )
        for route in routes
        if route.get("prefix") and route.get("upstream")
    ]

    return sorted(parsed_routes, key=lambda item: len(item.prefix), reverse=True)


def match_route(path: str, routes: list[ProxyRoute]) -> ProxyRoute | None:
    for route in routes:
        if path == route.prefix or path.startswith(f"{route.prefix}/"):
            return route
    return None


def strip_prefix(path: str, prefix: str) -> str:
    if path == prefix:
        return "/"

    stripped = path.removeprefix(prefix)
    return stripped if stripped.startswith("/") else f"/{stripped}"
