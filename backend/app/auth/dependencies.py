from __future__ import annotations

from fastapi import Cookie, Depends, Request
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.db.models import User
from app.db.session import get_db
from app.auth.service import get_session_by_token


SESSION_COOKIE_NAME = "session"


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> User:
    if session_token is None:
        raise AuthenticationError("missing")

    session = get_session_by_token(db, session_token)
    if session is None:
        raise AuthenticationError("invalid")

    user = db.get(User, session.user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("invalid")

    # Attach session for logout.
    request.state.session = session
    return user
