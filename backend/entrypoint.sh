#!/bin/sh
set -eu

# Ensure the SQLite volume directory is writable for the non-root app user.
# This runs as root; the application process itself is started as uid 10001.

APP_UID="10001"
APP_GID="10001"
DATA_DIR="/var/lib/app"

mkdir -p "$DATA_DIR"
chown -R "$APP_UID:$APP_GID" "$DATA_DIR"
chmod 700 "$DATA_DIR"

exec su -s /bin/sh -c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'" appuser
