from __future__ import annotations

import ipaddress
import threading
import time
from collections import defaultdict

from fastapi import HTTPException, Request


_static_lock = threading.Lock()
_static_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
_static_loaded = False

_dynamic_lock = threading.Lock()
_dynamic_blocked: dict[str, float] = {}  # {ip: unblock_at}

_failure_lock = threading.Lock()
_failure_windows: dict[str, list[float]] = defaultdict(list)


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


def _is_dynamically_blocked(ip: str) -> bool:
    with _dynamic_lock:
        unblock_at = _dynamic_blocked.get(ip)
        if unblock_at is None:
            return False
        if time.time() < unblock_at:
            return True
        del _dynamic_blocked[ip]
        return False


def record_failure(ip: str, window_seconds: int, threshold: int, block_duration: int) -> None:
    now = time.time()
    cutoff = now - window_seconds
    with _failure_lock:
        history = _failure_windows[ip]
        while history and history[0] < cutoff:
            history.pop(0)
        history.append(now)
        if len(history) >= threshold:
            with _dynamic_lock:
                _dynamic_blocked[ip] = now + block_duration
            history.clear()


def check_ip_block(request: Request, blocklist_csv: str, enabled: bool) -> None:
    if not enabled:
        return
    ip = request.client.host if request.client else None
    if not ip:
        return
    _load_static(blocklist_csv)
    if _is_statically_blocked(ip) or _is_dynamically_blocked(ip):
        raise HTTPException(status_code=403, detail="access denied")
