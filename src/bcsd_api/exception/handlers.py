from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .base import AppException


def register_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _handle(request: Request, exc: AppException) -> JSONResponse:
        body = {"error_code": exc.error_code, "message": exc.message}
        return JSONResponse(status_code=exc.status_code, content=body)
