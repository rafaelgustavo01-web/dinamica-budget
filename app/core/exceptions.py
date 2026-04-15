from fastapi import Request
from fastapi.responses import JSONResponse


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


async def dinamica_exception_handler(request: Request, exc: DinamicaException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
