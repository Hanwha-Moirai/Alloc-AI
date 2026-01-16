from fastapi import FastAPI

from config import settings
from interface.api.routes import router as api_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)
    return app


def run() -> None:
    import uvicorn

    uvicorn.run("rag.main:create_app", factory=True, host="0.0.0.0", port=8000)


app = create_app()
