from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class NexusError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: list = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)


class NotFoundError(NexusError):
    def __init__(self, resource: str, resource_id: str = ""):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found" + (f": {resource_id}" if resource_id else ""),
            status_code=404,
        )


class UnauthorizedError(NexusError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)


class ForbiddenError(NexusError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)


class ConflictError(NexusError):
    def __init__(self, message: str):
        super().__init__(code="CONFLICT", message=message, status_code=409)


def _error_body(code: str, message: str, details: list = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NexusError)
    async def nexus_error_handler(request: Request, exc: NexusError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body("HTTP_ERROR", exc.detail),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("VALIDATION_ERROR", "Request validation failed", details),
        )
