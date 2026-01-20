#!/bin/sh
set -eu

# Canonical smoke test: runs *inside Docker network* using curl container.
# Works the same on Linux/macOS/Windows (via WSL/Git Bash), avoids JSON quoting issues.

docker compose up -d --build

docker compose --profile test run --rm curl
