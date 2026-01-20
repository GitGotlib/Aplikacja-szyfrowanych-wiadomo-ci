Ten katalog przechowuje certyfikat i klucz prywatny TLS używane przez NGINX (TLS termination).

Wymagane pliki (nie są częścią repozytorium):

- DEV (`TLS_MODE=dev`):
	- tls.crt — certyfikat X.509 (PEM)
	- tls.key — klucz prywatny (PEM)
	- ca.crt — lokalny dev CA (PEM) używany do podpisania tls.crt (opcjonalne, do zaufania w systemie)

- PROD (`TLS_MODE=prod`):
	- fullchain.pem — certyfikat łańcuch (PEM)
	- privkey.pem — klucz prywatny (PEM)

Uzasadnienie:
- Repozytorium nie może zawierać kluczy prywatnych.
- NGINX realizuje wymuszenie HTTPS oraz polityki nagłówków bezpieczeństwa na brzegu systemu.

Generowanie certyfikatu DEV dla localhost (cert serwera podpisany lokalnym CA):

- Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\docker\generate-dev-tls.ps1`
- Linux/macOS: `sh ./docker/generate-dev-tls.sh`

Wynik: `nginx/certs/tls.crt` i `nginx/certs/tls.key`

Uwaga:
- jeśli chcesz uniknąć ostrzeżeń w przeglądarce, dodaj `ca.crt` do zaufanych CA w systemie/przeglądarce.
- do testów `curl` możesz użyć `-k` lub wskazać CA: `--cacert nginx/certs/ca.crt`.
