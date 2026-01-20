from __future__ import annotations

import base64
from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="forbid")

    app_env: str = Field(default="production", alias="APP_ENV")
    app_name: str = Field(default="secure-messaging-poc", alias="APP_NAME")

    public_base_url: AnyUrl = Field(alias="PUBLIC_BASE_URL")
    cors_allow_origins: str = Field(default="https://localhost", alias="CORS_ALLOW_ORIGINS")

    sqlite_path: str = Field(default="/var/lib/app/app.sqlite3", alias="SQLITE_PATH")

    max_attachment_bytes: int = Field(default=25 * 1024 * 1024, alias="MAX_ATTACHMENT_BYTES")
    max_recipients_per_message: int = Field(default=25, alias="MAX_RECIPIENTS_PER_MESSAGE")

    login_rate_limit_per_minute: int = Field(default=10, alias="LOGIN_RATE_LIMIT_PER_MINUTE")

    cookie_secure: bool = Field(default=True, alias="COOKIE_SECURE")
    cookie_samesite: str = Field(default="strict", alias="COOKIE_SAMESITE")

    # Required secrets (base64-encoded 32 bytes)
    app_secret_key: str = Field(alias="APP_SECRET_KEY")
    data_key: str = Field(alias="DATA_KEY")
    totp_key_encryption_key: str = Field(alias="TOTP_KEY_ENCRYPTION_KEY")
    user_hmac_key_encryption_key: str = Field(alias="USER_HMAC_KEY_ENCRYPTION_KEY")

    # Auth/session
    session_ttl_seconds: int = Field(default=60 * 60 * 8, alias="SESSION_TTL_SECONDS")

    # Account lockout (defense-in-depth)
    max_failed_logins: int = Field(default=10, alias="MAX_FAILED_LOGINS")
    lockout_seconds: int = Field(default=10 * 60, alias="LOCKOUT_SECONDS")

    def _decode_32b_b64(self, value: str, field_name: str) -> bytes:
        try:
            raw = base64.b64decode(value, validate=True)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"{field_name} must be base64") from exc
        if len(raw) != 32:
            raise ValueError(f"{field_name} must decode to 32 bytes")
        return raw

    @property
    def data_key_bytes(self) -> bytes:
        return self._decode_32b_b64(self.data_key, "DATA_KEY")

    @property
    def totp_kek_bytes(self) -> bytes:
        return self._decode_32b_b64(self.totp_key_encryption_key, "TOTP_KEY_ENCRYPTION_KEY")

    @property
    def user_hmac_kek_bytes(self) -> bytes:
        return self._decode_32b_b64(self.user_hmac_key_encryption_key, "USER_HMAC_KEY_ENCRYPTION_KEY")


settings = Settings()
