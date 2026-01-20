from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.twofa.schemas import TwoFaSetupResponse, TwoFaStatusResponse, TwoFaVerifyRequest
from app.twofa.service import disable_totp, enable_totp, setup_totp


router = APIRouter(prefix="/2fa", tags=["2fa"])


@router.get("/status", response_model=TwoFaStatusResponse)
def status(current_user: User = Depends(get_current_user)) -> TwoFaStatusResponse:
    return TwoFaStatusResponse(enabled=bool(current_user.totp_enabled))


@router.post("/setup", response_model=TwoFaSetupResponse)
def setup(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> TwoFaSetupResponse:
    secret, uri = setup_totp(db, current_user)
    return TwoFaSetupResponse(secret=secret, provisioning_uri=uri)


@router.post("/enable")
def enable(payload: TwoFaVerifyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    enable_totp(db, current_user, payload.code)
    return {"ok": True}


@router.post("/disable")
def disable(payload: TwoFaVerifyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    disable_totp(db, current_user, payload.code)
    return {"ok": True}
