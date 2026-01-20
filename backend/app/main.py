from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.init import init_sqlite_schema
from app.middlewares.error_handler import error_handling_middleware
from app.middlewares.origin import origin_check_middleware
from app.middlewares.request_id import request_id_middleware
from app.middlewares.content_type import content_type_guard_middleware
from app.users.router import router as users_router
from app.auth.router import router as auth_router
from app.twofa.router import router as twofa_router
from app.messages.router import router as messages_router


def _parse_origins(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(",") if v.strip()]


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title=settings.app_name)

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        # Keep 422 for actual validation errors.
        # Treat malformed JSON (common on Windows curl/Powershell) as 400 with a clear message.
        errors = exc.errors() or []
        if any((e.get("type") == "json_invalid") for e in errors):
            request_id = getattr(request.state, "request_id", None)
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Invalid JSON body. Ensure valid JSON and Content-Type: application/json.",
                },
                headers={"X-Request-Id": request_id} if request_id else None,
            )

        return JSONResponse(status_code=422, content={"detail": "Validation failed", "errors": errors})

    # CORS is needed for browser-based frontend.
    allow_origins = _parse_origins(settings.cors_allow_origins)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    # Middlewares (order matters): request id -> origin check -> content type -> error normalization.
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(origin_check_middleware)
    app.middleware("http")(content_type_guard_middleware)
    app.middleware("http")(error_handling_middleware)

    @app.on_event("startup")
    def _startup() -> None:
        # Fail-fast check: decode secrets at startup for clear logs.
        _ = settings.app_secret_key_bytes
        _ = settings.data_key_bytes
        _ = settings.totp_kek_bytes
        _ = settings.user_hmac_kek_bytes

        init_sqlite_schema()

    # Routers
    app.include_router(auth_router, prefix="/api")
    app.include_router(users_router, prefix="/api")
    app.include_router(twofa_router, prefix="/api")
    app.include_router(messages_router, prefix="/api")

    return app


app = create_app()
