from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, LoginResponse, LogoutResponse
from app.auth.service import authenticate_user, create_session, revoke_session
from app.auth.dependencies import SESSION_COOKIE_NAME, get_current_user
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.db.session import get_db
from app.db.models import User
from app.middlewares.rate_limit import FixedWindowRateLimiter


router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory per-IP limiter for login attempts.
_login_limiter = FixedWindowRateLimiter(window_seconds=60, max_requests=settings.login_rate_limit_per_minute)


def _client_ip(request: Request) -> str:
    # Behind NGINX: X-Real-IP is set. Fallback to client host.
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    _login_limiter.check(f"login:{_client_ip(request)}")

    # Always return minimal information.
    try:
        user = authenticate_user(db, email=str(payload.email), password=payload.password, totp_code=payload.totp_code)
    except AuthenticationError:
        # If user exists and has 2FA, we still do not leak it.
        raise

    token, _session = create_session(db, user, ip_address=_client_ip(request), user_agent=request.headers.get("User-Agent"))

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/",
        max_age=settings.session_ttl_seconds,
    )
    return LoginResponse(requires_2fa=False)


@router.post("/logout", response_model=LogoutResponse)
def logout(request: Request, response: Response, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> LogoutResponse:
    session = getattr(request.state, "session", None)
    if session is not None:
        revoke_session(db, session)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return LogoutResponse(ok=True)
