from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.crud import get_all_memory, get_posts_with_analytics
from backend.db.database import SessionLocal
from backend.db.models import Post
from backend.rag.vector_store import KNOWLEDGE_COLLECTION, USER_POSTS_COLLECTION, query_documents

# Higher temperature for creative writing
draft_llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.9,
)


@tool
def get_my_posts(state: Annotated[dict, InjectedState]) -> str:
    """
    Get the user's published posts and their engagement data (likes, comments, shares).
    Use this when the user asks how their posts are performing, what's getting traction,
    which topics work best, or when making data-driven content recommendations.
    """
    user_id = state["user_id"]
    db: Session = SessionLocal()
    try:
        posts_data = get_posts_with_analytics(db, user_id)
        if not posts_data:
            return "No published posts yet. Once you publish a post, engagement data will appear here."

        lines = ["## Your Published Posts\n"]
        total_likes = 0
        total_comments = 0
        total_shares = 0

        for item in posts_data:
            post = item["post"]
            a = item["analytics"]
            likes = a.likes if a else 0
            comments = a.comments if a else 0
            shares = a.shares if a else 0
            total_likes += likes
            total_comments += comments
            total_shares += shares

            preview = post.content[:150].replace("\n", " ").strip() + "..."
            published = post.published_at.strftime("%b %d, %Y") if post.published_at else "unknown date"
            fetched = f" (data as of {a.fetched_at.strftime('%b %d')})" if a else " (no analytics fetched yet)"

            lines.append(f"**[{published}]** {preview}")
            lines.append(f"  {likes} likes · {comments} comments · {shares} shares{fetched}\n")

        lines.append(f"---\nTotals across {len(posts_data)} posts: {total_likes} likes · {total_comments} comments · {total_shares} shares")
        return "\n".join(lines)
    finally:
        db.close()


@tool
def draft_post(
    topic: str,
    format: str,
    state: Annotated[dict, InjectedState],
) -> str:
    """
    Write a full LinkedIn post draft and save it for the user to review.
    Use this when the user asks you to write or draft a post.
    The user will decide whether to publish or schedule it — never publish automatically.

    Args:
        topic: what the post is about (be specific)
        format: one of 'story', 'list', 'hot_take', 'project_breakdown'
    """
    user_id = state["user_id"]
    db: Session = SessionLocal()

    try:
        memory = get_all_memory(db, user_id)

        kb_context = query_documents(KNOWLEDGE_COLLECTION, f"{format} post about {topic}", n_results=3)
        past_posts = query_documents(USER_POSTS_COLLECTION, topic, n_results=2)

        memory_context = f"\nUser context: {memory}" if memory else ""
        kb_context_str = "\n\n".join(kb_context) if kb_context else ""
        past_posts_str = "\n---\n".join(past_posts) if past_posts else "No past posts yet."

        system = SystemMessage(content=f"""You are a LinkedIn ghostwriter for a software engineer.
Write exactly one LinkedIn post. No preamble, no explanation — just the post itself, ready to publish.

Format requested: {format}
Topic: {topic}
{memory_context}

LinkedIn best practices to apply:
{kb_context_str}

User's past posts for style reference (match this voice if available):
{past_posts_str}

Rules:
- Start with a strong hook (first line must stop the scroll)
- Write in first person, conversational tone
- No buzzwords, no corporate language
- End with either a question or a clear call to action
- 3-5 hashtags at the very end
- Length: 150-300 words for story/hot_take, 200-400 for list/project_breakdown
""")

        response = draft_llm.invoke([system, HumanMessage(content=f"Write a {format} post about: {topic}")])
        post_content = response.content

        # Save as draft — user decides what to do with it
        post = Post(
            user_id=user_id,
            content=post_content,
            status="draft",
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        return f"Here's your draft (saved with ID {post.id}):\n\n{post_content}\n\n---\nReview it and let me know if you'd like any changes. When you're happy with it, publish or schedule it from the app."

    finally:
        db.close()
