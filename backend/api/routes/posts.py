from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.crud import get_posts_with_analytics, upsert_analytics
from backend.db.database import get_db
from backend.db.models import Post, User
from backend.linkedin.client import LinkedInClient
from backend.rag.ingestion import ingest_user_post

router = APIRouter(prefix="/posts", tags=["posts"])
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


class ScheduleRequest(BaseModel):
    token: str
    post_id: str
    publish_at: str  # ISO format: "2025-05-01T09:00:00"


@router.get("/drafts")
def get_drafts(token: str, db: Session = Depends(get_db)):
    """Get all draft posts — shown in the frontend for review."""
    user = get_current_user(token, db)
    drafts = db.query(Post).filter(
        Post.user_id == user.id,
        Post.status == "draft"
    ).order_by(Post.created_at.desc()).all()

    return [{"id": str(p.id), "content": p.content, "created_at": str(p.created_at)} for p in drafts]


@router.post("/publish/{post_id}")
async def publish_post(post_id: str, token: str, db: Session = Depends(get_db)):
    """
    Publish a saved draft to LinkedIn.
    User explicitly triggers this — the agent never calls this.
    """
    user = get_current_user(token, db)

    post = db.query(Post).filter(Post.id == post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.status != "draft":
        raise HTTPException(status_code=400, detail=f"Post is already {post.status}")

    client = LinkedInClient(user.access_token)
    author_urn = f"urn:li:person:{user.linkedin_id}"
    result = await client.publish_post(author_urn, post.content)

    linkedin_post_id = result.get("id", "unknown")
    post.status = "published"
    post.linkedin_post_id = linkedin_post_id
    post.published_at = datetime.now(timezone.utc)
    db.commit()

    # Add to ChromaDB so agent learns your voice over time
    ingest_user_post(
        post_content=post.content,
        post_id=str(post.id),
        metadata={"published_at": str(post.published_at), "topic": "general"},
    )

    return {"message": "Published successfully", "linkedin_post_id": linkedin_post_id}


@router.post("/schedule")
def schedule_post(request: ScheduleRequest, db: Session = Depends(get_db)):
    """
    Schedule a draft for future publishing.
    User explicitly picks the time — the agent never calls this.
    """
    user = get_current_user(request.token, db)

    post = db.query(Post).filter(Post.id == request.post_id, Post.user_id == user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.status != "draft":
        raise HTTPException(status_code=400, detail=f"Post is already {post.status}")

    scheduled_time = datetime.fromisoformat(request.publish_at)
    post.status = "scheduled"
    post.scheduled_at = scheduled_time
    db.commit()

    return {"message": f"Scheduled for {scheduled_time.strftime('%B %d at %I:%M %p')}"}


@router.get("/scheduled")
def get_scheduled(token: str, db: Session = Depends(get_db)):
    """Get all scheduled posts."""
    user = get_current_user(token, db)
    posts = db.query(Post).filter(
        Post.user_id == user.id,
        Post.status == "scheduled"
    ).order_by(Post.scheduled_at.asc()).all()

    return [{"id": str(p.id), "content": p.content, "scheduled_at": str(p.scheduled_at)} for p in posts]


@router.get("/published")
def get_published(token: str, db: Session = Depends(get_db)):
    """Get all published posts."""
    user = get_current_user(token, db)
    posts = db.query(Post).filter(
        Post.user_id == user.id,
        Post.status == "published"
    ).order_by(Post.published_at.desc()).all()

    return [{"id": str(p.id), "content": p.content, "published_at": str(p.published_at)} for p in posts]


@router.post("/analytics/refresh")
async def refresh_analytics(token: str, db: Session = Depends(get_db)):
    """Fetch latest engagement data from LinkedIn for all published posts."""
    user = get_current_user(token, db)
    posts = db.query(Post).filter(
        Post.user_id == user.id,
        Post.status == "published",
        Post.linkedin_post_id.isnot(None),
    ).all()

    client = LinkedInClient(user.access_token)
    refreshed = []

    for post in posts:
        stats = await client.get_post_analytics(post.linkedin_post_id)
        upsert_analytics(db, post.id, **stats)
        refreshed.append({"post_id": str(post.id), **stats})

    return {"refreshed": len(refreshed), "posts": refreshed}


@router.get("/analytics")
def get_analytics(token: str, db: Session = Depends(get_db)):
    """Get all published posts with their latest engagement data."""
    user = get_current_user(token, db)
    posts_data = get_posts_with_analytics(db, user.id)

    return [
        {
            "id": str(item["post"].id),
            "content": item["post"].content,
            "published_at": str(item["post"].published_at),
            "likes": item["analytics"].likes if item["analytics"] else 0,
            "comments": item["analytics"].comments if item["analytics"] else 0,
            "shares": item["analytics"].shares if item["analytics"] else 0,
            "impressions": item["analytics"].impressions if item["analytics"] else 0,
            "fetched_at": str(item["analytics"].fetched_at) if item["analytics"] else None,
        }
        for item in posts_data
    ]
