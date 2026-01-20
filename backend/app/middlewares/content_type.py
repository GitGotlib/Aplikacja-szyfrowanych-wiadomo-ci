from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse


_JSON_CT = "application/json"
_ALLOWED_CT_PREFIXES = (
    "application/json",
    "multipart/form-data",
    "application/x-www-form-urlencoded",
)


async def content_type_guard_middleware(request: Request, call_next):
    """Fail fast with 415 on clearly wrong Content-Type for API write requests.

    This prevents confusing 422 errors when the client sends a body but forgets
    `Content-Type: application/json`.

    We keep it intentionally simple and path-based (only /api) to avoid magic.
    """

    if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        has_body = content_length not in (None, "", "0")

        if has_body:
            ct = (request.headers.get("content-type") or "").strip().lower()
            if ct and any(ct.startswith(prefix) for prefix in _ALLOWED_CT_PREFIXES):
                return await call_next(request)

            # No Content-Type or an unsupported one.
            request_id = getattr(request.state, "request_id", None)
            headers = {"X-Request-Id": request_id} if request_id else None
            return JSONResponse(
                status_code=415,
                content={"detail": f"Unsupported Content-Type. Use '{_JSON_CT}'."},
                headers=headers,
            )

    return await call_next(request)
