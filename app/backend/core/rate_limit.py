"""
Simple rate limiter for auth endpoints.
Uses slowapi (in-memory storage) — no external dependencies needed.
Appropriate for on-premise single-server deployments.

For multi-worker (Gunicorn) deployments, configure a Redis backend:
  limiter = Limiter(key_func=_get_client_ip, storage_uri="redis://localhost:6379")
"""

from starlette.requests import Request

from slowapi import Limiter


def _get_client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For behind reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the chain is the original client
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# key_func=_get_client_ip: rate limits by real client IP (proxy-aware)
# default_limits=[]: no global limit — limits applied per-route only
limiter = Limiter(key_func=_get_client_ip, default_limits=[])
