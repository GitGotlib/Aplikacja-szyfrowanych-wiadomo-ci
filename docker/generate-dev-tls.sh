#!/bin/sh
set -eu

# Generates a self-signed TLS cert for DEV into nginx/certs/ using a throwaway container.
# Output files:
# - nginx/certs/tls.crt
# - nginx/certs/tls.key

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT_DIR/nginx/certs"

mkdir -p "$CERT_DIR"

docker run --rm -v "$CERT_DIR:/out" alpine:3.19 sh -lc \
  "apk add --no-cache openssl >/dev/null; \
   openssl req -x509 -nodes -newkey rsa:2048 \
     -keyout /out/tls.key -out /out/tls.crt -days 365 \
     -subj '/CN=localhost'"

echo "Generated: $CERT_DIR/tls.crt"
echo "Generated: $CERT_DIR/tls.key"
