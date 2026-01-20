from __future__ import annotations

import json
import secrets
import sys
from dataclasses import dataclass

import httpx
import pyotp


@dataclass
class Cfg:
    base_url: str = "https://nginx"


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    cfg = Cfg()

    origin = "https://localhost"

    rnd = secrets.token_hex(4)
    email = f"u{rnd}@example.com"
    username = f"user{rnd}"
    password = "CorrectHorseBatteryStaple!1"

    print(f"[e2e] base_url={cfg.base_url}")
    print(f"[e2e] user={email} / {username}")

    with httpx.Client(base_url=cfg.base_url, verify=False, timeout=20.0) as client:
        # Register
        r = client.post(
            "/api/auth/register",
            json={"email": email, "username": username, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code not in (200, 201):
            die(f"[e2e] register failed: {r.status_code} {r.text}")

        # Login (no 2FA yet) => should set cookie
        r = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            die(f"[e2e] login failed: {r.status_code} {r.text}")
        body = r.json()
        if body.get("requires_2fa") is True:
            die(f"[e2e] unexpected requires_2fa on fresh account: {body}")

        # Confirm session works
        r = client.get("/api/users/me")
        if r.status_code != 200:
            die(f"[e2e] me failed after login: {r.status_code} {r.text}")

        # Setup 2FA (returns secret + provisioning_uri)
        r = client.post(
            "/api/2fa/setup",
            json={},
            headers={"Content-Type": "application/json", "Origin": origin},
        )
        if r.status_code != 200:
            die(f"[e2e] 2fa setup failed: {r.status_code} {r.text}")
        setup = r.json()
        secret = setup.get("secret")
        if not isinstance(secret, str) or not secret:
            die(f"[e2e] setup did not return secret: {json.dumps(setup)}")

        # Enable 2FA using a valid current TOTP code
        code = pyotp.TOTP(secret).now()
        r = client.post(
            "/api/2fa/enable",
            json={"code": code},
            headers={"Content-Type": "application/json", "Origin": origin},
        )
        if r.status_code != 200:
            die(f"[e2e] 2fa enable failed: {r.status_code} {r.text}")

        # Logout
        r = client.post(
            "/api/auth/logout",
            json={},
            headers={"Content-Type": "application/json", "Origin": origin},
        )
        if r.status_code != 200:
            die(f"[e2e] logout failed: {r.status_code} {r.text}")

        # Clear cookies explicitly
        client.cookies.clear()

        # Login should now require 2FA but NOT set session cookie
        r = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            die(f"[e2e] login(2fa-required) failed: {r.status_code} {r.text}")
        body = r.json()
        if body.get("requires_2fa") is not True:
            die(f"[e2e] expected requires_2fa=true, got: {body}")
        if "set-cookie" in {k.lower() for k in r.headers.keys()}:
            die("[e2e] login returned Set-Cookie even though 2FA was required")

        # Complete login with /login/2fa
        code2 = pyotp.TOTP(secret).now()
        r = client.post(
            "/api/auth/login/2fa",
            json={"email": email, "password": password, "totp_code": code2},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            die(f"[e2e] login/2fa failed: {r.status_code} {r.text}")

        # Me should work again
        r = client.get("/api/users/me")
        if r.status_code != 200:
            die(f"[e2e] me failed after 2fa login: {r.status_code} {r.text}")

        # Anti-replay: the same code must NOT be accepted twice in the same step.
        client.cookies.clear()
        r = client.post(
            "/api/auth/login/2fa",
            json={"email": email, "password": password, "totp_code": code2},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code == 200:
            die("[e2e] TOTP replay was accepted (expected rejection)")

        print("[e2e] OK")


if __name__ == "__main__":
    main()
