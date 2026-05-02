"""Rate limiting middleware for clinical-chat service."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    Limits: 10 requests per minute per user/IP
    """

    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_history = defaultdict(list)  # {identifier: [timestamp, ...]}

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health" or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Extract client identifier (user_id from token, or IP)
        identifier = self._get_identifier(request)

        # Check rate limit
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Clean old requests
        self.request_history[identifier] = [
            ts for ts in self.request_history[identifier] if ts > cutoff
        ]

        # Check if over limit
        if len(self.request_history[identifier]) >= self.requests_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                extra={"identifier": identifier, "count": len(self.request_history[identifier])},
            )
            return JSONResponse(
                {"detail": "Rate limit exceeded: 10 requests per minute"},
                status_code=429,
            )

        # Record this request
        self.request_history[identifier].append(now)

        return await call_next(request)

    def _get_identifier(self, request: Request) -> str:
        """Extract user identifier for rate limiting."""
        # Try to get user_id from token/auth
        try:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                # In production, decode JWT and extract user_id
                return auth_header[7:20]  # Simplified for MVP
        except Exception:
            pass

        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip_{client_ip}"
