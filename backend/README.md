Backend (Python + FastAPI) zawiera całą logikę biznesową i kryptograficzną.

Założenia:
- brak kryptografii po stronie klienta,
- szyfrowanie i HMAC są realizowane wyłącznie na serwerze,
- dane w SQLite są przechowywane w postaci zaszyfrowanej (ciphertext + nonce + tag),
- sekrety (klucze główne, klucze szyfrujące sekrety TOTP/HMAC) nie są przechowywane w repozytorium.
