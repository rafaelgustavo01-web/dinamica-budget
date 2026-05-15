import logging
import sys

import structlog

from backend.core.config import settings


def _build_console_handler(log_level: int) -> logging.Handler:
    if settings.DEBUG or settings.RICH_TRACEBACKS:
        try:
            from rich.logging import RichHandler
            from rich.traceback import install as install_rich_traceback

            install_rich_traceback(show_locals=False, suppress=[structlog])
            handler = RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=False,
                show_path=True,
                markup=False,
            )
            handler.setLevel(log_level)
            return handler
        except Exception:
            pass

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    return handler


def configure_logging() -> None:
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if not settings.DEBUG
            else structlog.dev.ConsoleRenderer(
                exception_formatter=structlog.dev.RichTracebackFormatter(show_locals=False),
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        handlers=[_build_console_handler(log_level)],
        level=log_level,
        force=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
