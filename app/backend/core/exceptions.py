from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.logging import get_logger
from backend.core.observability import REQUEST_ID_HEADER, get_request_id

logger = get_logger(__name__)


class DinamicaException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(DinamicaException):
    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} '{identifier}' não encontrado.",
            status_code=404,
        )


class AuthenticationError(DinamicaException):
    def __init__(self, message: str = "Credenciais inválidas.") -> None:
        super().__init__(code="AUTHENTICATION_ERROR", message=message, status_code=401)


class AuthorizationError(DinamicaException):
    def __init__(self, message: str = "Acesso não autorizado.") -> None:
        super().__init__(code="AUTHORIZATION_ERROR", message=message, status_code=403)


class ConflictError(DinamicaException):
    def __init__(self, resource: str, field: str, value: str) -> None:
        super().__init__(
            code=f"{resource.upper()}_CONFLICT",
            message=f"{resource} com {field}='{value}' já existe.",
            status_code=409,
        )


class ValidationError(DinamicaException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code="VALIDATION_ERROR", message=message, status_code=422, details=details
        )


class UnprocessableEntityError(DinamicaException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code="UNPROCESSABLE_ENTITY", message=message, status_code=422, details=details
        )


def _api_error_content(
    *,
    code: str,
    message: str,
    request_id: str,
    details: dict | None = None,
) -> dict:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        },
        "request_id": request_id,
    }


async def dinamica_exception_handler(request: Request, exc: DinamicaException) -> JSONResponse:
    request_id = get_request_id(request)
    if exc.status_code >= 500:
        logger.error("dinamica_exception", code=exc.code, status_code=exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        headers={REQUEST_ID_HEADER: request_id},
        content=_api_error_content(
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ),
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = get_request_id(request)
    if exc.status_code >= 500:
        logger.error("http_exception", status_code=exc.status_code, detail=str(exc.detail))
    return JSONResponse(
        status_code=exc.status_code,
        headers={REQUEST_ID_HEADER: request_id},
        content={
            "detail": exc.detail,
            "request_id": request_id,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    request_id = get_request_id(request)
    logger.warning("request_validation_error", error_count=len(exc.errors()))
    return JSONResponse(
        status_code=422,
        headers={REQUEST_ID_HEADER: request_id},
        content={
            "detail": exc.errors(),
            "request_id": request_id,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = get_request_id(request)
    logger.error(
        "unhandled_exception",
        error_type=exc.__class__.__name__,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        headers={REQUEST_ID_HEADER: request_id},
        content=_api_error_content(
            code="INTERNAL_SERVER_ERROR",
            message="Erro interno ao processar a operação. Informe o código abaixo ao suporte.",
            request_id=request_id,
        ),
    )
