from __future__ import annotations

import ipaddress
import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request


# ---------------------------------------------------------------------------
# Static blocklist
# ---------------------------------------------------------------------------

_static_lock = threading.Lock()
_static_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
_static_loaded = False


def _load_static(blocklist_csv: str) -> None:
    global _static_loaded
    with _static_lock:
        if _static_loaded:
            return
        for cidr in blocklist_csv.split(","):
            cidr = cidr.strip()
            if cidr:
                try:
                    _static_networks.append(ipaddress.ip_network(cidr, strict=False))
                except ValueError:
                    pass
        _static_loaded = True


def _is_statically_blocked(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _static_networks)


# ---------------------------------------------------------------------------
# Dynamic blocks + offense tracking (for progressive duration)
# ---------------------------------------------------------------------------

_dynamic_lock = threading.Lock()
_dynamic_blocked: dict[str, float] = {}  # ip -> unblock_at

_offense_lock = threading.Lock()
_offense_count: dict[str, int] = defaultdict(int)  # ip -> cumulative offense count

_BLOCK_DURATIONS = [15 * 60, 60 * 60, 24 * 60 * 60]  # 15 min → 1 h → 24 h


def _is_dynamically_blocked(ip: str) -> bool:
    with _dynamic_lock:
        unblock_at = _dynamic_blocked.get(ip)
        if unblock_at is None:
            return False
        if time.time() < unblock_at:
            return True
        del _dynamic_blocked[ip]
        return False


def _next_block_duration(ip: str) -> int:
    with _offense_lock:
        count = _offense_count[ip]
        return _BLOCK_DURATIONS[min(count, len(_BLOCK_DURATIONS) - 1)]


# ---------------------------------------------------------------------------
# Anomaly scoring (sliding window, weighted per signal type)
# ---------------------------------------------------------------------------

_score_lock = threading.Lock()
_score_events: dict[str, list[tuple[float, int]]] = defaultdict(list)  # ip -> [(ts, points)]


def record_score(ip: str, points: int, window_seconds: int, threshold: int) -> None:
    """
    Accumulate anomaly points for an IP within a sliding window.
    Triggers a progressive-duration block when the score reaches threshold.

    Signal weights (caller's responsibility):
      route scanning (404 on unknown path)  → 1 pt
      bad request / fuzzing (400)           → 1 pt
      authz probing (403 after valid JWT)   → 2 pts
    """
    now = time.time()
    cutoff = now - window_seconds
    with _score_lock:
        events = _score_events[ip]
        while events and events[0][0] < cutoff:
            events.pop(0)
        events.append((now, points))
        score = sum(p for _, p in events)
        if score >= threshold:
            duration = _next_block_duration(ip)
            with _dynamic_lock:
                _dynamic_blocked[ip] = now + duration
            with _offense_lock:
                _offense_count[ip] += 1
            events.clear()


# ---------------------------------------------------------------------------
# Client IP resolution (trusted-proxy-aware)
# ---------------------------------------------------------------------------

def get_client_ip(request: Request, trusted_proxies: int = 1) -> str:
    """
    Resolve the real client IP from X-Forwarded-For, accounting for
    the configured number of trusted reverse proxies in the chain.

    X-Forwarded-For: <client>, <proxy1>, <proxy2>
    Each proxy appends itself on the right. With trusted_proxies=1
    (single nginx ingress), the real client is at index len-2 (or [0]
    if only one entry exists).
    """
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        ips = [s.strip() for s in forwarded_for.split(",")]
        idx = max(0, len(ips) - trusted_proxies - 1)
        candidate = ips[idx]
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            pass
    real_ip = request.headers.get("x-real-ip", "")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# Check (called at request ingress)
# ---------------------------------------------------------------------------

def check_ip_block(ip: str, blocklist_csv: str, enabled: bool) -> None:
    if not enabled:
        return
    _load_static(blocklist_csv)
    if _is_statically_blocked(ip) or _is_dynamically_blocked(ip):
        raise HTTPException(status_code=403, detail="access denied")


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

def list_blocks() -> list[dict]:
    now = time.time()
    with _dynamic_lock:
        return [
            {
                "ip": ip,
                "unblocks_at": int(unblock_at),
                "seconds_remaining": max(0, int(unblock_at - now)),
            }
            for ip, unblock_at in _dynamic_blocked.items()
            if unblock_at > now
        ]


def unblock(ip: str) -> bool:
    removed = False
    with _dynamic_lock:
        if ip in _dynamic_blocked:
            del _dynamic_blocked[ip]
            removed = True
    with _score_lock:
        _score_events.pop(ip, None)
    return removed


def unblock_all() -> int:
    with _dynamic_lock:
        count = len(_dynamic_blocked)
        _dynamic_blocked.clear()
    with _score_lock:
        _score_events.clear()
    return count
