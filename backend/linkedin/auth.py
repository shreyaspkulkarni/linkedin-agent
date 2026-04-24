import secrets
from urllib.parse import urlencode

import httpx

from backend.config import settings

AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = "openid profile email w_member_social"

# In-memory state store for CSRF protection (use Redis in production)
_state_store: set[str] = set()


def generate_auth_url() -> tuple[str, str]:
    """Returns (auth_url, state) — store state to verify on callback."""
    state = secrets.token_urlsafe(32)
    _state_store.add(state)

    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "scope": SCOPES,
        "state": state,
    }
    return f"{AUTHORIZATION_URL}?{urlencode(params)}", state


def verify_state(state: str) -> bool:
    if state in _state_store:
        _state_store.discard(state)
        return True
    return False


async def exchange_code_for_token(code: str) -> dict:
    """Exchange OAuth code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.linkedin_redirect_uri,
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()


async def get_linkedin_profile(access_token: str) -> dict:
    """Fetch authenticated user's profile via OpenID Connect userinfo endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()
