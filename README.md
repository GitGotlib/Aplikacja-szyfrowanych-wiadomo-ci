# Aplikacja szyfrowanych wiadomości (POC)

Projekt: FastAPI (backend) + NGINX (reverse proxy z terminacją TLS) uruchamiane w Docker Compose.

Założenie bezpieczeństwa: cała kryptografia jest po stronie backendu.

## Szybki start (zalecany, idiotoodporny)

### 0) Wymagania

- Docker Desktop + Docker Compose v2

### 1) Sekrety (wymagane)

Ten projekt **nie ma** bezpiecznych domyślnych kluczy. Jeśli ich nie podasz, Compose przerwie uruchomienie.

1. Skopiuj przykład: `copy .env.example .env`
2. Wygeneruj sekrety (Windows): `powershell -ExecutionPolicy Bypass -File .\docker\generate-secrets.ps1`
3. Wklej wartości do `.env` (4 zmienne: `APP_SECRET_KEY`, `DATA_KEY`, `TOTP_KEY_ENCRYPTION_KEY`, `USER_HMAC_KEY_ENCRYPTION_KEY`).

### 2) TLS (DEV)

NGINX w trybie DEV używa self-signed certów:
- wymagane pliki: `nginx/certs/tls.crt` oraz `nginx/certs/tls.key`

Generacja:
- Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\docker\generate-dev-tls.ps1`
- Linux/macOS: `sh ./docker/generate-dev-tls.sh`

### 3) Uruchomienie

`docker compose up -d --build`

### 4) Oficjalny smoke-test (kanoniczny sposób testowania)

Ten test:
- działa identycznie na Windows/Linux/macOS,
- nie ma problemów z quotingiem JSON (payload tworzy się w kontenerze),
- testuje **przez NGINX** (zalecane).

Uruchom:
- Windows: `powershell -ExecutionPolicy Bypass -File .\docker\smoke-test.ps1`
- Linux/macOS: `sh ./docker/smoke-test.sh`

Co robi test:
- `POST /api/users/register`
- `POST /api/auth/login` (cookie session)
- `GET /api/users/me`
- `GET /healthz`

## Architektura i ścieżki HTTP

### Publiczne ścieżki (przez NGINX)

- `https://localhost/healthz` – health-check
- `https://localhost/api/...` – API backendu
- `https://localhost/` – frontend (UI)

Ważne:
- backend montuje routery pod prefiksem `/api`
- NGINX **nie przepisuje** ścieżek (brak „magii” z ucinaniem `/api`)

## TLS: DEV vs PROD

Projekt rozdziela tryby przez zmienne w `.env`:

- `TLS_MODE=dev` + `NGINX_CONFIG_FILE=nginx.conf`
	- oczekiwane: `nginx/certs/tls.crt`, `nginx/certs/tls.key`
- `TLS_MODE=prod` + `NGINX_CONFIG_FILE=nginx.prod.conf`
	- oczekiwane: `nginx/certs/fullchain.pem`, `nginx/certs/privkey.pem`

NGINX startuje z kontrolą obecności certów. Jeśli brakuje plików, kontener **kończy pracę z czytelnym komunikatem** (zamiast nieczytelnego błędu OpenSSL).

## Testowanie: opcja wewnętrzna (bez NGINX)

To jest opcjonalne i służy diagnostyce.

Przykład (wewnątrz sieci Dockera):

`docker compose --profile test run --rm curl sh -lc "curl -sS http://backend:8000/api/users/me -i"`

Uwaga: backend zakłada HTTPS/cookie Secure w typowym scenariuszu przez NGINX, więc to jest głównie do sprawdzenia routingu i odpowiedzi.

## Punkt wejścia backendu (FastAPI)

Jedynym ASGI entrypointem aplikacji jest:

- `app.main:app`

W kontenerze i lokalnie import `app` jest stabilny, bo backend jest instalowany jako pakiet (`pip install -e backend`).

## Walidacja i błędy (intencjonalne zachowanie)

- `415 Unsupported Content-Type` – gdy wysyłasz body do `/api` bez `Content-Type: application/json`
- `400 Invalid JSON body` – gdy body nie jest poprawnym JSON (np. quoting/encoding)
- `422 Validation failed` – gdy JSON jest poprawny, ale nie spełnia schematu (np. brak pola)

W trybie nieprodukcyjnym odpowiedzi 500 zawierają `error_type` (bez stack trace), żeby nie maskować błędów deweloperskich.

## Struktura repo

- `backend/` – backend FastAPI + kryptografia
- `nginx/` – reverse proxy, TLS termination
- `database/` – wersjonowany schemat SQLite
- `docker/` – skrypty uruchomieniowe (sekrety, certy DEV, smoke-test)

