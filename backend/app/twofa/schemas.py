from __future__ import annotations

from pydantic import BaseModel, Field


class TwoFaSetupResponse(BaseModel):
    # Returned once, for enrollment.
    secret: str
    provisioning_uri: str


class TwoFaVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8, pattern=r"^[0-9]+$")


class TwoFaStatusResponse(BaseModel):
    enabled: bool
