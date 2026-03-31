import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .auth.router import router as auth_router
from .dependencies import get_authz, get_settings
from .exception import register_handlers
from .redirect import router as redirect_router

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
    _init_pg(settings)
    try:
        _init_spicedb(settings)
    except Exception:
        logger.warning("SpiceDB unavailable, skipping schema init")
    yield


def _init_pg(settings) -> None:
    from sqlalchemy import text

    from .core.database import create_engine

    engine = create_engine(settings.database_url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    engine.dispose()
    logger.info("PostgreSQL connected")


def create_app() -> FastAPI:
    app = FastAPI(
        title="BCSD API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )
    settings = get_settings()
    from .core import slack_log
    slack_log.setup(settings.slack_bot_token, settings.slack_error_channel)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_handlers(app)
    app.include_router(auth_router)
    app.include_router(redirect_router)
    _mount_graphql(app)
    return app


def _mount_graphql(app: FastAPI) -> None:
    from strawberry.fastapi import GraphQLRouter

    from .graphql.context import context_getter
    from .graphql.schema import schema

    router = GraphQLRouter(schema, context_getter=context_getter, graphql_ide=None)
    app.include_router(router, prefix="/graphql")


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
