import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .base import AppException

root_logger = logging.getLogger()


def register_handlers(app: FastAPI) -> None:
    app.add_middleware(ErrorAlertMiddleware)

    @app.exception_handler(AppException)
    async def _handle(request: Request, exc: AppException) -> JSONResponse:
        body = {"error_code": exc.error_code, "message": exc.message}
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        root_logger.error(
            "%s %s: %s", request.method, request.url.path, exc, exc_info=exc,
        )
        body = {"error_code": "INTERNAL_ERROR", "message": "internal server error"}
        return JSONResponse(status_code=500, content=body)


class ErrorAlertMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            root_logger.error(
                "%s %s: %s", request.method, request.url.path, exc, exc_info=exc,
            )
            raise
