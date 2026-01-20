<#
Generuje 4 sekrety (32 bajty) w base64 dla lokalnego uruchomienia.

Użycie:
  pwsh -File .\docker\generate-secrets.ps1

Wynik wklej do pliku .env (NIE commituj .env):
  APP_SECRET_KEY=...
  DATA_KEY=...
  TOTP_KEY_ENCRYPTION_KEY=...
  USER_HMAC_KEY_ENCRYPTION_KEY=...
#>

function New-Base64Key32 {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    return [Convert]::ToBase64String($bytes)
}

"APP_SECRET_KEY=$(New-Base64Key32)"
"DATA_KEY=$(New-Base64Key32)"
"TOTP_KEY_ENCRYPTION_KEY=$(New-Base64Key32)"
"USER_HMAC_KEY_ENCRYPTION_KEY=$(New-Base64Key32)"
