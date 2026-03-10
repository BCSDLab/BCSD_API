import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .dependencies import get_authz, get_settings, get_sheets
from .exception import register_handlers
from .member.router import router as member_router
from .track import router as track_router

logger = logging.getLogger(__name__)

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "spicedb" / "schema.zed"


def _init_spicedb(settings) -> None:
    if not SCHEMA_PATH.exists():
        logger.warning("SpiceDB schema not found: %s", SCHEMA_PATH)
        return
    authz = get_authz(settings)
    authz.write_schema(SCHEMA_PATH.read_text())
    logger.info("SpiceDB schema loaded")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    sheets = get_sheets(settings)
    sheets.init_sheets()
    from .sheets.defaults import seed
    seed(sheets)
    try:
        _init_spicedb(settings)
    except Exception:
        logger.warning("SpiceDB unavailable, skipping schema init")
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
