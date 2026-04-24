from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.database import get_db
from backend.db.models import User
from backend.linkedin.client import LinkedInClient

router = APIRouter(prefix="/profile", tags=["profile"])

ALGORITHM = "HS256"


def get_current_user(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me")
async def get_my_profile(token: str, db: Session = Depends(get_db)):
    """Return the authenticated user's LinkedIn profile."""
    user = get_current_user(token, db)
    client = LinkedInClient(user.access_token)
    profile = await client.get_profile()
    return profile
