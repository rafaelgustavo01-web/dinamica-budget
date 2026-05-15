from __future__ import annotations

import contextvars
import re
import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request
from starlette.responses import Response

from backend.core.logging import get_logger

REQUEST_ID_HEADER = "X-Request-ID"
CLIENT_REQUEST_ID_HEADER = "X-Client-Request-ID"

_request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)

logger = get_logger(__name__)

_SAFE_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{8,80}$")


def _new_request_id() -> str:
    return "req_" + uuid.uuid4().hex[:12]


def _safe_request_id(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip()
    if _SAFE_REQUEST_ID_RE.match(value):
        return value
    return None


def get_request_id(request: Request | None = None) -> str:
    if request is not None:
        request_id = getattr(request.state, "request_id", None)
        if isinstance(request_id, str) and request_id:
            return request_id
    return _request_id_ctx.get() or _new_request_id()


def classify_operation(path: str) -> str | None:
    if "/smart-import" in path:
        return "planilha.smart_import"
    if "/pq/" in path or path.endswith("/pq"):
        if "/match" in path:
            return "planilha.pq_match"
        if "/importar" in path:
            return "planilha.pq_import"
        return "planilha.pq"
    if "/busca" in path or "/servicos" in path or "/composicoes" in path:
        return "tcpo.busca"
    if "/cpu" in path or "/histograma" in path:
        return "cpu.calculo"
    if "/bcu" in path and ("importar" in path or "upload" in path):
        return "planilha.bcu_import"
    return None


def _request_id_from_headers(request: Request) -> str:
    incoming = (
        _safe_request_id(request.headers.get(REQUEST_ID_HEADER))
        or _safe_request_id(request.headers.get(CLIENT_REQUEST_ID_HEADER))
    )
    return incoming or _new_request_id()


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = _request_id_from_headers(request)
    operation = classify_operation(request.url.path)
    started_at = time.perf_counter()

    request.state.request_id = request_id
    token = _request_id_ctx.set(request_id)
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        operation=operation,
        method=request.method,
        path=request.url.path,
    )

    try:
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id

        if response.status_code >= 500:
            logger.error(
                "request_failed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
        elif operation and response.status_code >= 400:
            logger.warning(
                "request_rejected",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
        elif operation:
            logger.info(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

        return response
    finally:
        structlog.contextvars.clear_contextvars()
        _request_id_ctx.reset(token)
