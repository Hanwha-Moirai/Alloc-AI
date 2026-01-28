import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi_pagination import add_pagination

from config import settings
from interface.api.routes import router as api_router

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.append(str(_repo_root))


def create_app() -> FastAPI:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title=settings.app_name)
    app.include_router(api_router)
    add_pagination(app)
    return app


def run() -> None:
    import uvicorn

    uvicorn.run("rag.main:create_app", factory=True, host="0.0.0.0", port=8000)


app = create_app()
