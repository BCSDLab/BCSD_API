from fastapi import FastAPI

from .auth.router import router as auth_router
from .exception import register_handlers
from .member.router import router as member_router


def create_app() -> FastAPI:
    app = FastAPI(title="BCSDLab API", version="0.1.0")
    register_handlers(app)
    app.include_router(auth_router)
    app.include_router(member_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("bcsd_api.main:app", host="0.0.0.0", port=8000, reload=True)
