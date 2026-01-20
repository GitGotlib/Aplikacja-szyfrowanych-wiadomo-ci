from __future__ import annotations

import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


_password_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=64 * 1024,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def validate_password_strength(password: str) -> None:
    """Deny-by-default minimal policy suitable for academic POC."""

    if len(password) < 12:
        raise ValueError("Password too short")

    # Require diversity: lower, upper, digit, special.
    rules = [
        (r"[a-z]", "lowercase"),
        (r"[A-Z]", "uppercase"),
        (r"[0-9]", "digit"),
        (r"[^A-Za-z0-9]", "special"),
    ]
    for pattern, _name in rules:
        if re.search(pattern, password) is None:
            raise ValueError("Password does not meet complexity requirements")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
