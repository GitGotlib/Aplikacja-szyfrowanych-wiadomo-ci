Ten katalog przechowuje certyfikat i klucz prywatny TLS używane przez NGINX (TLS termination).

Wymagane pliki (nie są częścią repozytorium):

- DEV (`TLS_MODE=dev`):
	- tls.crt — certyfikat X.509 (PEM)
	- tls.key — klucz prywatny (PEM)

- PROD (`TLS_MODE=prod`):
	- fullchain.pem — certyfikat łańcuch (PEM)
	- privkey.pem — klucz prywatny (PEM)

Uzasadnienie:
- Repozytorium nie może zawierać kluczy prywatnych.
- NGINX realizuje wymuszenie HTTPS oraz polityki nagłówków bezpieczeństwa na brzegu systemu.

Generowanie certyfikatu DEV (self-signed) dla localhost:

- Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\docker\generate-dev-tls.ps1`
- Linux/macOS: `sh ./docker/generate-dev-tls.sh`

Wynik: `nginx/certs/tls.crt` i `nginx/certs/tls.key`

Uwaga:
- certyfikat self-signed nie będzie zaufany przez przeglądarkę; do testów `curl` użyj flagi `-k`.
