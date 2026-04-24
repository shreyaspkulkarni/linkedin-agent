from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.crud import create_or_update_user
from backend.db.database import get_db
from backend.linkedin.auth import exchange_code_for_token, generate_auth_url, get_linkedin_profile, verify_state

router = APIRouter(prefix="/auth", tags=["auth"])

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30


def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


@router.get("/login")
async def login():
    """Redirect user to LinkedIn OAuth."""
    auth_url, _ = generate_auth_url()
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle LinkedIn OAuth callback, create user, return JWT."""
    if not verify_state(state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_data = await exchange_code_for_token(code)
    access_token = token_data["access_token"]

    profile = await get_linkedin_profile(access_token)

    user = create_or_update_user(
        db=db,
        linkedin_id=profile["sub"],
        name=profile.get("name", ""),
        email=profile.get("email", ""),
        profile_picture=profile.get("picture", ""),
        access_token=access_token,
    )

    jwt_token = create_jwt(str(user.id))

    # Redirect to frontend callback page with token in query param
    return RedirectResponse(url=f"{settings.frontend_url}/auth/callback?token={jwt_token}")
