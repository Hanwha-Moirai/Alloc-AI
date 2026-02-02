import logging

from fastapi import FastAPI

from pdf.controller.routes import router as pdf_router


def create_app() -> FastAPI:
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(title="pdf-service")
    app.include_router(pdf_router)
    return app


def run() -> None:
    import uvicorn

    uvicorn.run("pdf.main:create_app", factory=True, host="0.0.0.0", port=8010)


app = create_app()
