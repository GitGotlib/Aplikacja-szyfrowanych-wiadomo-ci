from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ValidationError
from app.crypto.aes_gcm import AesGcmCipher
from app.crypto.key_management import generate_hmac_key
from app.crypto.passwords import hash_password
from app.db.models import User, utcnow
from app.core.config import settings


def create_user(db: Session, email: str, username: str, password: str) -> User:
    email_norm = email.strip().lower()
    username_norm = username.strip()

    existing = db.execute(select(User).where((User.email == email_norm) | (User.username == username_norm))).scalar_one_or_none()
    if existing is not None:
        # Avoid user enumeration via registration endpoint.
        raise ValidationError("Registration failed")

    user_id = str(uuid.uuid4())

    try:
        password_hash = hash_password(password)
    except ValueError as exc:
        # Preserve the policy but return a controlled client error.
        raise ValidationError(str(exc)) from exc
    now = utcnow()

    # Per-user HMAC key is generated server-side and stored encrypted at rest.
    hmac_key = generate_hmac_key()
    cipher = AesGcmCipher(settings.user_hmac_kek_bytes)
    aad = f"users:hmac_key:{user_id}".encode("utf-8")
    enc = cipher.encrypt(hmac_key, aad=aad)

    user = User(
        id=user_id,
        email=email_norm,
        username=username_norm,
        password_hash=password_hash,
        password_updated_at=now,
        totp_enabled=False,
        totp_secret_enc=None,
        totp_secret_nonce=None,
        totp_secret_tag=None,
        hmac_key_enc=enc.ciphertext,
        hmac_key_nonce=enc.nonce,
        hmac_key_tag=enc.tag,
        is_active=True,
        failed_login_count=0,
        locked_until=None,
        last_login_at=None,
        created_at=now,
        updated_at=now,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: str) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    email_norm = email.strip().lower()
    return db.execute(select(User).where(User.email == email_norm)).scalar_one_or_none()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.execute(select(User).where(User.username == username.strip())).scalar_one_or_none()


def is_locked(user: User) -> bool:
    if user.locked_until is None:
        return False
    return user.locked_until > dt.datetime.now(dt.UTC)
