from __future__ import annotations

import threading
import time
from collections import defaultdict

_lock = threading.Lock()
_attempts: dict[str, list[float]] = defaultdict(list)  # {ip: [timestamps]}
_lockouts: dict[str, float] = {}  # {ip: unlock_at}

_WINDOW_SECONDS = 60
_SOFT_THRESHOLD = 5    # failures → short lockout
_HARD_THRESHOLD = 15   # cumulative failures → long lockout
_SOFT_LOCKOUT = 300    # 5 minutes
_HARD_LOCKOUT = 3600   # 1 hour


def is_locked_out(ip: str) -> tuple[bool, int]:
    """Returns (locked, retry_after_seconds)."""
    now = time.time()
    with _lock:
        unlock_at = _lockouts.get(ip)
        if unlock_at is None:
            return False, 0
        if now < unlock_at:
            return True, int(unlock_at - now) + 1
        del _lockouts[ip]
    return False, 0


def record_failure(ip: str) -> None:
    now = time.time()
    cutoff = now - _WINDOW_SECONDS
    with _lock:
        history = _attempts[ip]
        while history and history[0] < cutoff:
            history.pop(0)
        history.append(now)
        count = len(history)
        if count >= _SOFT_THRESHOLD:
            duration = _HARD_LOCKOUT if count >= _HARD_THRESHOLD else _SOFT_LOCKOUT
            _lockouts[ip] = now + duration
            history.clear()


def record_success(ip: str) -> None:
    with _lock:
        _attempts.pop(ip, None)
        _lockouts.pop(ip, None)
