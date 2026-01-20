#!/bin/sh
set -eu

# Generates a DEV TLS cert for nginx/certs/ signed by a local dev CA.
# Output files:
# - nginx/certs/tls.crt
# - nginx/certs/tls.key

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT_DIR/nginx/certs"

mkdir -p "$CERT_DIR"

docker run --rm -v "$CERT_DIR:/out" alpine:3.19 sh -lc \
  "set -eu; apk add --no-cache openssl >/dev/null; \
   openssl req -x509 -nodes -newkey rsa:2048 \
     -keyout /out/ca.key -out /out/ca.crt -days 3650 \
     -subj '/CN=Politechnika Dev CA/O=Politechnika/OU=student'; \
   openssl req -new -nodes -newkey rsa:2048 \
     -keyout /out/tls.key -out /out/tls.csr \
     -subj '/CN=localhost/O=GotlibCorp/OU=Hlib'; \
   printf '%s\n' \
     '[req]' \
     'distinguished_name=req_distinguished_name' \
     '[req_distinguished_name]' \
     '[v3_req]' \
     'basicConstraints=CA:FALSE' \
     'keyUsage=digitalSignature,keyEncipherment' \
     'extendedKeyUsage=serverAuth' \
     'subjectAltName=@alt_names' \
     '[alt_names]' \
     'DNS.1=localhost' \
     'IP.1=127.0.0.1' \
     > /out/tls.ext; \
   openssl x509 -req -in /out/tls.csr \
     -CA /out/ca.crt -CAkey /out/ca.key -CAcreateserial \
     -out /out/tls.leaf.crt -days 365 -sha256 \
     -extfile /out/tls.ext -extensions v3_req; \
   cat /out/tls.leaf.crt /out/ca.crt > /out/tls.crt; \
   rm -f /out/tls.csr /out/tls.ext /out/tls.leaf.crt /out/ca.srl"

echo "Generated: $CERT_DIR/tls.crt"
echo "Generated: $CERT_DIR/tls.key"
echo "Generated: $CERT_DIR/ca.crt (local dev CA)"
