from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppError, AuthenticationError, AuthorizationError, IntegrityError, RateLimitError, ValidationError


logger = logging.getLogger("app.errors")


async def error_handling_middleware(request: Request, call_next):
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-Id") or ""

    try:
        response = await call_next(request)
        if request_id:
            response.headers.setdefault("X-Request-Id", request_id)
        return response
    except RateLimitError:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"}, headers={"X-Request-Id": request_id})
    except (AuthenticationError, AuthorizationError):
        return JSONResponse(status_code=401, content={"detail": "Authentication required"}, headers={"X-Request-Id": request_id})
    except ValidationError:
        return JSONResponse(status_code=400, content={"detail": "Invalid request"}, headers={"X-Request-Id": request_id})
    except IntegrityError:
        return JSONResponse(status_code=400, content={"detail": "Integrity check failed"}, headers={"X-Request-Id": request_id})
    except AppError:
        return JSONResponse(status_code=400, content={"detail": "Request rejected"}, headers={"X-Request-Id": request_id})
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled error", extra={"path": str(request.url.path), "request_id": request_id})
        if settings.app_env.lower() != "production":
            return JSONResponse(
                status_code=500,
                content={"detail": "Unhandled server error", "error_type": exc.__class__.__name__},
                headers={"X-Request-Id": request_id} if request_id else None,
            )
        return JSONResponse(status_code=500, content={"detail": "Server error"}, headers={"X-Request-Id": request_id})
