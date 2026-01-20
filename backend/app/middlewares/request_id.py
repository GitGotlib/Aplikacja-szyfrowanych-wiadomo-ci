from __future__ import annotations

import uuid

from fastapi import Request


async def request_id_middleware(request: Request, call_next):
    # This is a small helper; main error middleware also ensures request_id is present.
    if not hasattr(request.state, "request_id"):
        request.state.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers.setdefault("X-Request-Id", request.state.request_id)
    return response
