Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Canonical smoke test: runs *inside Docker network* using curl container.
# Works reliably on Windows PowerShell because the JSON is generated inside the container.

docker compose up -d --build

docker compose --profile test run --rm curl
