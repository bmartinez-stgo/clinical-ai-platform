from __future__ import annotations

import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request


_lock = threading.Lock()
_windows: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> None:
    now = time.time()
    cutoff = now - window_seconds
    with _lock:
        history = _windows[key]
        # drop expired entries
        while history and history[0] < cutoff:
            history.pop(0)
        if len(history) >= limit:
            # oldest entry tells us when the window reopens
            retry_after = int(history[0] + window_seconds - now) + 1
            raise HTTPException(
                status_code=429,
                detail="rate limit exceeded",
                headers={"Retry-After": str(max(retry_after, 1))},
            )
        history.append(now)


def ip_key(request: Request, prefix: str, trusted_proxies: int = 1) -> str:
    from app.middleware.ip_block import get_client_ip
    ip = get_client_ip(request, trusted_proxies)
    return f"ip:{ip}:{prefix}"


def user_key(subject: str, prefix: str) -> str:
    return f"user:{subject}:{prefix}"
