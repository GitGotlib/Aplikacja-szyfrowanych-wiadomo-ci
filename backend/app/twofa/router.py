from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.models import User
from app.db.session import get_db
from app.middlewares.rate_limit import FixedWindowRateLimiter
from app.twofa.schemas import TwoFaSetupResponse, TwoFaStatusResponse, TwoFaVerifyRequest
from app.twofa.service import disable_totp, enable_totp, setup_totp


router = APIRouter(prefix="/2fa", tags=["2fa"])

_twofa_limiter = FixedWindowRateLimiter(window_seconds=60, max_requests=max(5, settings.login_rate_limit_per_minute))


def _client_ip(request: Request) -> str:
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


@router.get("/status", response_model=TwoFaStatusResponse)
def status(current_user: User = Depends(get_current_user)) -> TwoFaStatusResponse:
    return TwoFaStatusResponse(enabled=bool(current_user.totp_enabled))


@router.post("/setup", response_model=TwoFaSetupResponse)
def setup(response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TwoFaSetupResponse:
    response.headers["Cache-Control"] = "no-store"
    secret, uri = setup_totp(db, current_user)
    return TwoFaSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/enable")
def enable(payload: TwoFaVerifyRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    _twofa_limiter.check(f"2fa_enable:{_client_ip(request)}")
    enable_totp(db, current_user, payload.code)
    return {"ok": True}


@router.post("/disable")
def disable(payload: TwoFaVerifyRequest, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    _twofa_limiter.check(f"2fa_disable:{_client_ip(request)}")
    disable_totp(db, current_user, payload.code)
    return {"ok": True}
