from __future__ import annotations

import re

_MAX_FREE_TEXT = 1000
_MAX_SHORT_TEXT = 200

# Patterns covering common prompt injection techniques
_INJECTION_PATTERNS = [
    r"ignore\s.{0,30}(previous|instructions?|system|above|rules?)",
    r"(forget|disregard|override)\s.{0,30}(instructions?|rules?|context|above)",
    r"you\s+are\s+now\b",
    r"new\s+(instructions?|rules?|role|persona|task)",
    r"\bsystem\s*:",
    r"\bassistant\s*:",
    r"<\s*(system|instruction|prompt|s)\s*>",
    r"\[INST\]",
    r"###\s*(instruction|system|prompt|human|assistant)",
    r"<\|im_start\|>",
    r"<\|im_end\|>",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_free_text(text: str | None, max_len: int = _MAX_FREE_TEXT) -> str | None:
    if text is None:
        return None
    text = text[:max_len].strip()
    text = _INJECTION_RE.sub("[REDACTED]", text)
    return text


def sanitize_short_text(text: str | None) -> str | None:
    return sanitize_free_text(text, _MAX_SHORT_TEXT)


def sanitize_list(items: list[str] | None, max_len: int = _MAX_SHORT_TEXT) -> list[str]:
    if not items:
        return items or []
    return [sanitize_free_text(item, max_len) or "" for item in items]
