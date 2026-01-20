from __future__ import annotations

import datetime as dt
import hashlib
import secrets
import time
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.crypto.aes_gcm import AesGcmCipher
from app.crypto.passwords import verify_password
from app.crypto.totp import verify_totp_code
from app.db.models import User, UserSession, utcnow
from app.users.service import is_locked


def _hash_session_token(token: str) -> bytes:
    return hashlib.sha256(token.encode("utf-8")).digest()


def _random_delay_on_failure() -> None:
    # Deterministic, small delay to make online guessing harder.
    time.sleep(0.5)


def authenticate_user(db: Session, email: str, password: str, totp_code: str | None) -> User:
    # Uniform error surface: always raise AuthenticationError on auth failure.
    user = db.execute(select(User).where(User.email == email.strip().lower())).scalar_one_or_none()
    if user is None:
        _random_delay_on_failure()
        raise AuthenticationError("invalid")

    if not user.is_active or is_locked(user):
        _random_delay_on_failure()
        raise AuthenticationError("invalid")

    if not verify_password(password, user.password_hash):
        user.failed_login_count += 1
        if user.failed_login_count >= settings.max_failed_logins:
            user.locked_until = utcnow() + dt.timedelta(seconds=settings.lockout_seconds)
        user.updated_at = utcnow()
        db.commit()
        _random_delay_on_failure()
        raise AuthenticationError("invalid")

    # If TOTP is enabled, enforce it.
    if user.totp_enabled:
        if totp_code is None:
            _random_delay_on_failure()
            raise AuthenticationError("invalid")

        if user.totp_secret_enc is None or user.totp_secret_nonce is None or user.totp_secret_tag is None:
            _random_delay_on_failure()
            raise AuthenticationError("invalid")

        cipher = AesGcmCipher(settings.totp_kek_bytes)
        aad = f"users:totp_secret:{user.id}".encode("utf-8")
        secret = cipher.decrypt(user.totp_secret_enc, user.totp_secret_nonce, user.totp_secret_tag, aad=aad).decode("utf-8")
        if not verify_totp_code(secret, totp_code):
            user.failed_login_count += 1
            user.updated_at = utcnow()
            db.commit()
            _random_delay_on_failure()
            raise AuthenticationError("invalid")

    # Success: reset counters
    user.failed_login_count = 0
    user.locked_until = None
    user.last_login_at = utcnow()
    user.updated_at = utcnow()
    db.commit()
    return user


def create_session(db: Session, user: User, ip_address: str | None, user_agent: str | None) -> tuple[str, UserSession]:
    token = secrets.token_urlsafe(32)
    token_hash = _hash_session_token(token)

    now = utcnow()
    session = UserSession(
        id=str(uuid.uuid4()),
        user_id=user.id,
        session_token_hash=token_hash,
        created_at=now,
        expires_at=now + dt.timedelta(seconds=settings.session_ttl_seconds),
        revoked_at=None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return token, session


def revoke_session(db: Session, session: UserSession) -> None:
    session.revoked_at = utcnow()
    db.commit()


def get_session_by_token(db: Session, token: str) -> UserSession | None:
    token_hash = _hash_session_token(token)
    now = utcnow()
    return (
        db.execute(
            select(UserSession)
            .where(UserSession.session_token_hash == token_hash)
            .where(UserSession.revoked_at.is_(None))
            .where(UserSession.expires_at > now)
        ).scalar_one_or_none()
    )
