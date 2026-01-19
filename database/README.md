Warstwa danych oparta o SQLite.

Zawartość:
- schema.sql: definicja relacyjnego schematu danych (tabele, relacje, kolumny bezpieczeństwa).

Uzasadnienie:
- schemat jest jawny i wersjonowany, aby umożliwić audyt i powtarzalne wdrożenia,
- dane wrażliwe są przechowywane wyłącznie jako ciphertext wraz z nonce/tag (AES-256-GCM) oraz HMAC (HMAC-SHA-256).
