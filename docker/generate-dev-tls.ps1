<#
Generuje DEV TLS cert dla lokalnego NGINX (localhost) podpisany lokalnym CA.

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

# Create a local CA (issuer): O=Politechnika, OU=student
# and a server cert (subject): O=GotlibCorp, OU=Hlib
# Include SANs required by modern clients.
docker run --rm -v "${pwdPath}:/out" alpine:3.19 sh -lc "set -eu; apk add --no-cache openssl >/dev/null; openssl req -x509 -nodes -newkey rsa:2048 -keyout /out/ca.key -out /out/ca.crt -days 3650 -subj '/CN=Politechnika Dev CA/O=Politechnika/OU=student'; openssl req -new -nodes -newkey rsa:2048 -keyout /out/tls.key -out /out/tls.csr -subj '/CN=localhost/O=GotlibCorp/OU=Hlib'; printf '%s\n' '[req]' 'distinguished_name=req_distinguished_name' '[req_distinguished_name]' '[v3_req]' 'basicConstraints=CA:FALSE' 'keyUsage=digitalSignature,keyEncipherment' 'extendedKeyUsage=serverAuth' 'subjectAltName=@alt_names' '[alt_names]' 'DNS.1=localhost' 'IP.1=127.0.0.1' > /out/tls.ext; openssl x509 -req -in /out/tls.csr -CA /out/ca.crt -CAkey /out/ca.key -CAcreateserial -out /out/tls.leaf.crt -days 365 -sha256 -extfile /out/tls.ext -extensions v3_req; cat /out/tls.leaf.crt /out/ca.crt > /out/tls.crt; rm -f /out/tls.csr /out/tls.ext /out/tls.leaf.crt /out/ca.srl"

Write-Host "Generated: $certDir\tls.crt"
Write-Host "Generated: $certDir\tls.key"
Write-Host "Generated: $certDir\ca.crt (local dev CA)"
Write-Host "Note: curl can use -k, or you can trust ca.crt in your OS/browser trust store."
