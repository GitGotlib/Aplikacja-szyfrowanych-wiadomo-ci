from __future__ import annotations

import time
import pyotp


def generate_totp_secret() -> str:
    # RFC 6238-compatible base32 secret
    return pyotp.random_base32()


def provisioning_uri(secret: str, account_name: str, issuer_name: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=account_name, issuer_name=issuer_name)


def verify_totp_code_and_step(secret: str, code: str, *, valid_window: int = 1) -> int | None:
    """Verify TOTP and return the accepted time-step counter.

    This allows callers to implement anti-replay (monotonic step enforcement).
    """

    totp = pyotp.TOTP(secret)
    otp = (code or "").strip()
    if not otp:
        return None

    now = time.time()
    for offset in range(-valid_window, valid_window + 1):
        t = int(now + (offset * totp.interval))
        try:
            if totp.verify(otp, for_time=t, valid_window=0):
                return int(t // totp.interval)
        except Exception:
            return None
    return None


def verify_totp_code(secret: str, code: str) -> bool:
    # valid_window=1 tolerates small clock drift
    return verify_totp_code_and_step(secret, code, valid_window=1) is not None
