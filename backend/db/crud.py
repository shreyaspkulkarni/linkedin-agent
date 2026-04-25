import json
from datetime import datetime

from sqlalchemy.orm import Session

from backend.db.models import Analytics, LinkedInProfile, Post, User, UserMemory


def get_user_by_linkedin_id(db: Session, linkedin_id: str) -> User | None:
    return db.query(User).filter(User.linkedin_id == linkedin_id).first()


def create_or_update_user(db: Session, linkedin_id: str, name: str, email: str,
                          profile_picture: str, access_token: str) -> User:
    user = get_user_by_linkedin_id(db, linkedin_id)
    if user:
        user.name = name
        user.email = email
        user.profile_picture = profile_picture
        user.access_token = access_token
    else:
        user = User(
            linkedin_id=linkedin_id,
            name=name,
            email=email,
            profile_picture=profile_picture,
            access_token=access_token,
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_memory(db: Session, user_id, key: str) -> str | None:
    record = db.query(UserMemory).filter(
        UserMemory.user_id == user_id,
        UserMemory.key == key
    ).first()
    return record.value if record else None


def set_memory(db: Session, user_id, key: str, value: str) -> UserMemory:
    record = db.query(UserMemory).filter(
        UserMemory.user_id == user_id,
        UserMemory.key == key
    ).first()
    if record:
        record.value = value
        record.updated_at = datetime.utcnow()
    else:
        record = UserMemory(user_id=user_id, key=key, value=value)
        db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_all_memory(db: Session, user_id) -> dict:
    records = db.query(UserMemory).filter(UserMemory.user_id == user_id).all()
    return {r.key: r.value for r in records}


def get_linkedin_profile_data(db: Session, user_id) -> LinkedInProfile | None:
    return db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user_id).first()


def save_linkedin_profile_data(
    db: Session, user_id, headline: str, about: str, experience: str, skills: str
) -> LinkedInProfile:
    record = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user_id).first()
    if record:
        record.headline = headline
        record.about = about
        record.experience = experience
        record.skills = skills
        record.updated_at = datetime.utcnow()
    else:
        record = LinkedInProfile(
            user_id=user_id,
            headline=headline,
            about=about,
            experience=experience,
            skills=skills,
        )
        db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_published_posts(db: Session, user_id, limit: int = 20) -> list[Post]:
    return (
        db.query(Post)
        .filter(Post.user_id == user_id, Post.status == "published")
        .order_by(Post.published_at.desc())
        .limit(limit)
        .all()
    )


def upsert_analytics(db: Session, post_id, likes: int, comments: int, shares: int, impressions: int = 0) -> Analytics:
    record = Analytics(post_id=post_id, likes=likes, comments=comments, shares=shares, impressions=impressions)
    db.add(record)
    db.commit()
    return record


def get_posts_with_analytics(db: Session, user_id, limit: int = 20) -> list[dict]:
    posts = get_published_posts(db, user_id, limit)
    result = []
    for post in posts:
        latest = (
            db.query(Analytics)
            .filter(Analytics.post_id == post.id)
            .order_by(Analytics.fetched_at.desc())
            .first()
        )
        result.append({"post": post, "analytics": latest})
    return result
