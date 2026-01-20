<#
Generuje self-signed TLS cert dla lokalnego NGINX (localhost).

Uzasadnienie:
- NGINX ma TLS termination (HTTPS-only), ale repo nie może zawierać kluczy prywatnych.
- Ten skrypt generuje pliki lokalnie do nginx/certs (katalog jest ignorowany przez git).

Wymagania:
- Docker musi działać lokalnie.

Użycie:
  powershell -ExecutionPolicy Bypass -File .\docker\generate-dev-tls.ps1

Wynik:
  nginx/certs/tls.crt
  nginx/certs/tls.key
#>

$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$certDir = Join-Path $root 'nginx\certs'
New-Item -ItemType Directory -Force -Path $certDir | Out-Null

# Use a small Alpine container to run OpenSSL without requiring it on the host.
$pwdPath = (Resolve-Path $certDir).Path

docker run --rm -v "${pwdPath}:/out" alpine:3.19 sh -lc "apk add --no-cache openssl; openssl req -x509 -nodes -newkey rsa:2048 -keyout /out/tls.key -out /out/tls.crt -days 365 -subj '/CN=localhost'"

Write-Host "Generated: $certDir\tls.crt"
Write-Host "Generated: $certDir\tls.key"
Write-Host "Note: Browsers/curl will treat this as self-signed; use -k for curl or add it to trusted store if desired."
