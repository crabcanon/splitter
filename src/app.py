from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI

from api.errors import splitter_error_handler, unhandled_error_handler
from api.routes import router
from core.config import Settings
from core.errors import SplitterError

__version__ = "0.1.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="Universal Document Parsing & Splitting Gateway",
        description="FastAPI service for routing document content to splitter strategies.",
        version=__version__,
        openapi_version="3.1.0",
    )
    app.include_router(router)
    app.add_exception_handler(SplitterError, splitter_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.state.settings = settings
    return app


app = create_app()


def run() -> None:
    uvicorn.run(
        "app:app",
        host=os.getenv("SPLITTER_HOST", "0.0.0.0"),
        port=int(os.getenv("SPLITTER_PORT", "8000")),
        reload=os.getenv("SPLITTER_RELOAD", "false").lower() == "true",
    )
