from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.users.schemas import MeResponse, RegisterRequest, RegisterResponse, UserPublic
from app.users.service import create_user
from app.auth.dependencies import get_current_user
from app.db.models import User


router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    user = create_user(db, email=payload.email, username=payload.username, password=payload.password)
    return RegisterResponse(user=UserPublic(id=user.id, email=user.email, username=user.username))


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(user=UserPublic(id=current_user.id, email=current_user.email, username=current_user.username))
