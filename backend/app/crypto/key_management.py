from __future__ import annotations

import os


def generate_aes256_key() -> bytes:
    return os.urandom(32)


def generate_hmac_key() -> bytes:
    return os.urandom(32)
