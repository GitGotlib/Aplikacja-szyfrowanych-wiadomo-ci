#!/bin/sh
set -eu

BASE_URL="${BASE_URL:-https://nginx}"

say() { printf '%s\n' "$*"; }

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required tool: $1" 1>&2
    exit 1
  }
}

need curl

TMP_DIR="/tmp/smoke"
mkdir -p "$TMP_DIR"

TS="$(date +%s)"
RND="${RANDOM:-0}"
EMAIL="u${TS}${RND}@example.com"
USERNAME="user${TS}${RND}"
PASSWORD="StrongPass!1234A"

say "[smoke] Base URL: $BASE_URL"
say "[smoke] Register: $EMAIL / $USERNAME"

cat >"$TMP_DIR/register.json" <<EOF
{"email":"$EMAIL","username":"$USERNAME","password":"$PASSWORD"}
EOF

REG_CODE="$(curl -sk -o "$TMP_DIR/register.out" -w '%{http_code}' \
  "$BASE_URL/api/users/register" \
  -H 'Content-Type: application/json' \
  --data-binary "@$TMP_DIR/register.json")"

if [ "$REG_CODE" != "200" ]; then
  say "[smoke] FAIL register: HTTP $REG_CODE"
  sed -n '1,200p' "$TMP_DIR/register.out" || true
  exit 1
fi

say "[smoke] Login"
cat >"$TMP_DIR/login.json" <<EOF
{"email":"$EMAIL","password":"$PASSWORD"}
EOF

LOGIN_CODE="$(curl -sk -o "$TMP_DIR/login.out" -w '%{http_code}' \
  -c "$TMP_DIR/cookies.txt" \
  "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  --data-binary "@$TMP_DIR/login.json")"

if [ "$LOGIN_CODE" != "200" ]; then
  say "[smoke] FAIL login: HTTP $LOGIN_CODE"
  sed -n '1,200p' "$TMP_DIR/login.out" || true
  exit 1
fi

say "[smoke] Me (authenticated)"
ME_CODE="$(curl -sk -o "$TMP_DIR/me.out" -w '%{http_code}' \
  -b "$TMP_DIR/cookies.txt" \
  "$BASE_URL/api/users/me")"

if [ "$ME_CODE" != "200" ]; then
  say "[smoke] FAIL me: HTTP $ME_CODE"
  sed -n '1,200p' "$TMP_DIR/me.out" || true
  exit 1
fi

say "[smoke] Healthz"
HZ_CODE="$(curl -sk -o "$TMP_DIR/healthz.out" -w '%{http_code}' \
  "$BASE_URL/healthz")"

if [ "$HZ_CODE" != "200" ]; then
  say "[smoke] FAIL healthz: HTTP $HZ_CODE"
  sed -n '1,200p' "$TMP_DIR/healthz.out" || true
  exit 1
fi

say "[smoke] OK"
