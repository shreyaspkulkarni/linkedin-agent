import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from backend.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    linkedin_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String)
    profile_picture = Column(String)
    access_token = Column(Text, nullable=False)
    token_expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    memory = relationship("UserMemory", back_populates="user", cascade="all, delete")
    posts = relationship("Post", back_populates="user", cascade="all, delete")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete")
    linkedin_profile = relationship("LinkedInProfile", back_populates="user", uselist=False, cascade="all, delete")


class UserMemory(Base):
    __tablename__ = "user_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key = Column(String, nullable=False)   # e.g. "career_goals", "target_role"
    value = Column(Text, nullable=False)   # JSON string
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="memory")


class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(Enum("draft", "scheduled", "published", name="post_status"), default="draft")
    linkedin_post_id = Column(String)
    scheduled_at = Column(DateTime)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="posts")
    analytics = relationship("Analytics", back_populates="post", cascade="all, delete")


class LinkedInProfile(Base):
    __tablename__ = "linkedin_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    headline = Column(Text, default="")
    about = Column(Text, default="")
    experience = Column(Text, default="")  # free-form: paste your bullets
    skills = Column(Text, default="")      # comma-separated
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="linkedin_profile")


class Analytics(Base):
    __tablename__ = "analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id"), nullable=False)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="analytics")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(Enum("user", "assistant", name="conv_role"), nullable=False)
    content = Column(Text, nullable=False)
    tool_calls = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
