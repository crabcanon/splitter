from __future__ import annotations

import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from core.errors import SplitterError


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or uuid.uuid4().hex


async def splitter_error_handler(request: Request, exc: SplitterError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": _request_id(request),
            }
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal Server Error",
                "request_id": _request_id(request),
            }
        },
    )
