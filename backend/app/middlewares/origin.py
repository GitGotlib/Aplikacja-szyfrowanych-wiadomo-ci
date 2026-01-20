from __future__ import annotations

from fastapi import Request

from app.core.config import settings
from app.core.exceptions import AuthorizationError


def _normalize_origin(origin: str) -> str:
    return origin.rstrip("/")


def _parse_allowed_origins(value: str) -> set[str]:
    # Comma-separated list.
    return {_normalize_origin(v.strip()) for v in (value or "").split(",") if v.strip()}


async def origin_check_middleware(request: Request, call_next):
    # When using cookie-based auth, protect state-changing methods against CSRF
    # via strict Origin checking. This assumes frontend is served from PUBLIC_BASE_URL.
    if request.url.path.startswith("/api/") and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        # Only enforce when a session cookie is present (i.e., browser-authenticated).
        cookie = request.headers.get("Cookie") or ""
        has_session_cookie = "session=" in cookie

        if has_session_cookie:
            origin = request.headers.get("Origin")
            if origin is None:
                raise AuthorizationError("Missing origin")

            allowed = _parse_allowed_origins(settings.cors_allow_origins)
            allowed.add(_normalize_origin(str(settings.public_base_url)))
            if _normalize_origin(origin) not in allowed:
                raise AuthorizationError("Invalid origin")

    return await call_next(request)
