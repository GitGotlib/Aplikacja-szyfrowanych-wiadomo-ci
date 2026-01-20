#!/bin/sh
set -eu

MODE="${TLS_MODE:-dev}"
CERT_DIR="/etc/nginx/certs"

fail() {
  echo "[nginx] TLS configuration error: $1" 1>&2
  echo "[nginx] MODE=$MODE" 1>&2
  echo "[nginx] Expected certs under: $CERT_DIR" 1>&2
  echo "[nginx] DEV: generate self-signed certs via docker/generate-dev-tls.(ps1|sh)" 1>&2
  echo "[nginx] PROD: mount real certs into nginx/certs (e.g., fullchain.pem + privkey.pem)" 1>&2
  exit 1
}

case "$MODE" in
  dev)
    [ -r "$CERT_DIR/tls.crt" ] || fail "Missing or unreadable $CERT_DIR/tls.crt"
    [ -r "$CERT_DIR/tls.key" ] || fail "Missing or unreadable $CERT_DIR/tls.key"
    ;;
  prod)
    [ -r "$CERT_DIR/fullchain.pem" ] || fail "Missing or unreadable $CERT_DIR/fullchain.pem"
    [ -r "$CERT_DIR/privkey.pem" ] || fail "Missing or unreadable $CERT_DIR/privkey.pem"
    ;;
  *)
    fail "Unknown TLS_MODE '$MODE' (use 'dev' or 'prod')"
    ;;
esac

exit 0
