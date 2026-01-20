from __future__ import annotations

import secrets
import sys

import httpx
import pyotp


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    base_url = "https://nginx"
    origin = "https://localhost"

    rnd = secrets.token_hex(4)
    email_rl = f"sec_rl{rnd}@example.com"
    username_rl = f"sec_rl{rnd}"

    email_csrf = f"sec_csrf{rnd}@example.com"
    username_csrf = f"sec_csrf{rnd}"
    password = "StrongPass!1234A"

    print(f"[sec] base_url={base_url}")
    print(f"[sec] user(rate-limit)={email_rl} / {username_rl}")
    print(f"[sec] user(csrf/2fa)={email_csrf} / {username_csrf}")

    with httpx.Client(base_url=base_url, verify=False, timeout=20.0) as client:
        for email, username in ((email_rl, username_rl), (email_csrf, username_csrf)):
            r = client.post(
                "/api/auth/register",
                json={"email": email, "username": username, "password": password},
                headers={"Content-Type": "application/json"},
            )
            if r.status_code not in (200, 201):
                die(f"[sec] register failed: {r.status_code} {r.text}")

        # Successful login (needed for cookie-auth CSRF/Origin checks).
        r = client.post(
            "/api/auth/login",
            json={"email": email_csrf, "password": password},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 200:
            die(f"[sec] login failed: {r.status_code} {r.text}")

        # CSRF/Origin enforcement: cookie-auth POST without Origin must be rejected
        r = client.post(
            "/api/2fa/setup",
            json={},
            headers={"Content-Type": "application/json"},
        )
        if r.status_code != 403:
            die(f"[sec] expected 403 Missing origin, got: {r.status_code} {r.text}")

        # 2FA setup with Origin should succeed
        r = client.post(
            "/api/2fa/setup",
            json={},
            headers={"Content-Type": "application/json", "Origin": origin},
        )
        if r.status_code != 200:
            die(f"[sec] 2fa setup failed: {r.status_code} {r.text}")
        secret = r.json().get("secret")
        if not isinstance(secret, str) or not secret:
            die("[sec] setup did not return secret")

        code = pyotp.TOTP(secret).now()
        r = client.post(
            "/api/2fa/enable",
            json={"code": code},
            headers={"Content-Type": "application/json", "Origin": origin},
        )
        if r.status_code != 200:
            die(f"[sec] 2fa enable failed: {r.status_code} {r.text}")

        # Brute-force / rate limit (wrong password).
        # Important: run this after the CSRF/2FA checks because the limiter is per-IP,
        # so intentionally exhausting it would break later authenticated requests.
        # Also ensure we're not sending a session cookie, otherwise the Origin middleware
        # may reject the request before the rate limiter is hit.
        client.cookies.clear()
        saw_429 = False
        rr = client.post(
            "/api/auth/login",
            json={"email": email_rl, "password": "WrongPass!1234A"},
            headers={"Content-Type": "application/json"},
        )
        if rr.status_code == 429:
            saw_429 = True
        else:
            for _ in range(1, 50):
                rr = client.post(
                    "/api/auth/login",
                    json={"email": email_rl, "password": "WrongPass!1234A"},
                    headers={"Content-Type": "application/json"},
                )
                if rr.status_code == 429:
                    saw_429 = True
                    break

        if not saw_429:
            die(f"[sec] expected login rate limit (429) but did not observe it (last={rr.status_code} {rr.text})")

    print("[sec] OK")


if __name__ == "__main__":
    main()
