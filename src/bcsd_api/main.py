from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .dependencies import get_settings, get_sheets
from .exception import register_handlers
from .member.router import router as member_router
from .track import router as track_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    sheets = get_sheets(settings)
    sheets.init_sheets()
    from .sheets.defaults import seed
    seed(sheets)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="BCSD API", version="0.1.0", lifespan=lifespan)
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_handlers(app)
    app.include_router(auth_router)
    app.include_router(member_router)
    app.include_router(track_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
