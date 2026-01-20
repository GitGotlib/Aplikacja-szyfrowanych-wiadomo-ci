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
from app.users.schemas import RegisterRequest, RegisterResponse, UserPublic
from app.users.service import create_user


router = APIRouter(prefix="/auth", tags=["auth"])

# In-memory per-IP limiter for login attempts.
_login_limiter = FixedWindowRateLimiter(window_seconds=60, max_requests=settings.login_rate_limit_per_minute)
_register_limiter = FixedWindowRateLimiter(window_seconds=60 * 60, max_requests=settings.register_rate_limit_per_hour)


def _client_ip(request: Request) -> str:
    # Behind NGINX: X-Real-IP is set. Fallback to client host.
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> RegisterResponse:
    ip = _client_ip(request)
    _register_limiter.check(f"register:ip:{ip}")
    _register_limiter.check(f"register:ip_email:{ip}:{str(payload.email).strip().lower()}")

    # Alias for /api/users/register (kept for clarity and backward compatibility).
    user = create_user(db, email=str(payload.email), username=payload.username, password=payload.password)
    return RegisterResponse(user=UserPublic(id=user.id, email=user.email, username=user.username))


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    ip = _client_ip(request)
    _login_limiter.check(f"login:ip:{ip}")
    _login_limiter.check(f"login:ip_email:{ip}:{str(payload.email).strip().lower()}")
    response.headers["Cache-Control"] = "no-store"

    user, requires_2fa = authenticate_user(
        db,
        email=str(payload.email),
        password=payload.password,
        totp_code=payload.totp_code,
        allow_2fa_challenge=True,
    )

    if requires_2fa:
        # Do NOT create a session cookie yet.
        return LoginResponse(requires_2fa=True)

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


@router.post("/login/2fa", response_model=LoginResponse)
def login_2fa(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> LoginResponse:
    ip = _client_ip(request)
    _login_limiter.check(f"login:ip:{ip}")
    _login_limiter.check(f"login:ip_email:{ip}:{str(payload.email).strip().lower()}")
    response.headers["Cache-Control"] = "no-store"

    # Here we require the second factor explicitly.
    user, requires_2fa = authenticate_user(
        db,
        email=str(payload.email),
        password=payload.password,
        totp_code=payload.totp_code,
        allow_2fa_challenge=False,
    )
    if requires_2fa:
        # Should never happen when allow_2fa_challenge=False.
        raise AuthenticationError("invalid")

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
    response.headers["Cache-Control"] = "no-store"
    session = getattr(request.state, "session", None)
    if session is not None:
        revoke_session(db, session)
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return LogoutResponse(ok=True)
