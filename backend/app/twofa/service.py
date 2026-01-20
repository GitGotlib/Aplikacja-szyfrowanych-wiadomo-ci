from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ValidationError
from app.crypto.aes_gcm import AesGcmCipher
from app.crypto.totp import generate_totp_secret, provisioning_uri, verify_totp_code_and_step
from app.db.models import User, utcnow


def setup_totp(db: Session, user: User) -> tuple[str, str]:
    secret = generate_totp_secret()

    cipher = AesGcmCipher(settings.totp_kek_bytes)
    aad = f"users:totp_secret:{user.id}".encode("utf-8")
    enc = cipher.encrypt(secret.encode("utf-8"), aad=aad)

    user.totp_secret_enc = enc.ciphertext
    user.totp_secret_nonce = enc.nonce
    user.totp_secret_tag = enc.tag

    # not enabled until verified
    user.totp_enabled = False
    user.totp_last_used_step = None
    user.updated_at = utcnow()
    db.commit()

    uri = provisioning_uri(secret=secret, account_name=user.email, issuer_name=settings.app_name)
    return secret, uri


def enable_totp(db: Session, user: User, code: str) -> None:
    if user.totp_secret_enc is None or user.totp_secret_nonce is None or user.totp_secret_tag is None:
        raise ValidationError("2FA not initialized")

    cipher = AesGcmCipher(settings.totp_kek_bytes)
    aad = f"users:totp_secret:{user.id}".encode("utf-8")
    secret = cipher.decrypt(user.totp_secret_enc, user.totp_secret_nonce, user.totp_secret_tag, aad=aad).decode("utf-8")

    step = verify_totp_code_and_step(secret, code, valid_window=1)
    if step is None:
        raise AuthenticationError("invalid")

    user.totp_enabled = True
    # Enrollment verification must not consume a login step.
    user.totp_last_used_step = None
    user.updated_at = utcnow()
    db.commit()


def disable_totp(db: Session, user: User, code: str) -> None:
    if not user.totp_enabled:
        return

    if user.totp_secret_enc is None or user.totp_secret_nonce is None or user.totp_secret_tag is None:
        raise AuthenticationError("invalid")

    cipher = AesGcmCipher(settings.totp_kek_bytes)
    aad = f"users:totp_secret:{user.id}".encode("utf-8")
    secret = cipher.decrypt(user.totp_secret_enc, user.totp_secret_nonce, user.totp_secret_tag, aad=aad).decode("utf-8")

    if verify_totp_code_and_step(secret, code, valid_window=1) is None:
        raise AuthenticationError("invalid")

    user.totp_enabled = False
    user.totp_secret_enc = None
    user.totp_secret_nonce = None
    user.totp_secret_tag = None
    user.totp_last_used_step = None
    user.updated_at = utcnow()
    db.commit()
