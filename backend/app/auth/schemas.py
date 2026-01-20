from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    totp_code: str | None = Field(default=None, min_length=6, max_length=8, pattern=r"^[0-9]+$")


class LoginResponse(BaseModel):
    # Session is delivered via HttpOnly cookie; body remains minimal.
    requires_2fa: bool = False


class LogoutResponse(BaseModel):
    ok: bool = True
