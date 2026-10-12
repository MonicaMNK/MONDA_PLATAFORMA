from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


def correlation_id(request: Request | None = None) -> str:
    if request is not None:
        existing = getattr(request.state, "correlation_id", None)
        if existing:
            return existing
    return str(uuid.uuid4())


def api_error(status: int, code: str, message: str, details: Any = None, request: Request | None = None) -> None:
    raise HTTPException(
        status_code=status,
        detail={"code": code, "message": message, "correlationId": correlation_id(request), "details": details},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and {"code", "message"}.issubset(exc.detail):
        payload = dict(exc.detail)
        payload.setdefault("correlationId", correlation_id(request))
    else:
        payload = {"code": "HTTP_ERROR", "message": str(exc.detail), "correlationId": correlation_id(request)}
    return JSONResponse(status_code=exc.status_code, content=payload)
