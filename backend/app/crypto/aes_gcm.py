from __future__ import annotations

import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass(frozen=True)
class AesGcmEncrypted:
    ciphertext: bytes  # without tag
    nonce: bytes
    tag: bytes


class AesGcmCipher:
    """AES-256-GCM helper that stores tag separately.

    Security notes:
    - nonce is generated randomly per encryption (96-bit),
    - tag is 128-bit (last 16 bytes returned by AESGCM.encrypt).
    """

    def __init__(self, key_32b: bytes):
        if len(key_32b) != 32:
            raise ValueError("AES-256 key must be 32 bytes")
        self._aesgcm = AESGCM(key_32b)

    def encrypt(self, plaintext: bytes, aad: bytes) -> AesGcmEncrypted:
        nonce = os.urandom(12)
        ct_and_tag = self._aesgcm.encrypt(nonce, plaintext, aad)
        if len(ct_and_tag) < 16:
            raise ValueError("ciphertext too short")
        return AesGcmEncrypted(
            ciphertext=ct_and_tag[:-16],
            nonce=nonce,
            tag=ct_and_tag[-16:],
        )

    def decrypt(self, ciphertext: bytes, nonce: bytes, tag: bytes, aad: bytes) -> bytes:
        return self._aesgcm.decrypt(nonce, ciphertext + tag, aad)
