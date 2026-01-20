from __future__ import annotations

import pyotp


def generate_totp_secret() -> str:
    # RFC 6238-compatible base32 secret
    return pyotp.random_base32()


def provisioning_uri(secret: str, account_name: str, issuer_name: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_name, issuer_name=issuer_name)


def verify_totp_code(secret: str, code: str) -> bool:
    # valid_window=1 tolerates small clock drift
    totp = pyotp.TOTP(secret)
    try:
        return totp.verify(code, valid_window=1)
    except Exception:
        return False
