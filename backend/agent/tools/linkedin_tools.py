from typing import Annotated

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy.orm import Session

from backend.config import settings
from backend.db.crud import get_all_memory, get_linkedin_profile_data
from backend.db.database import SessionLocal
from backend.db.models import User
from backend.linkedin.client import LinkedInClient
from backend.rag.vector_store import KNOWLEDGE_COLLECTION, query_documents

coach_llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.3,
)


@tool
async def get_linkedin_profile(state: Annotated[dict, InjectedState]) -> str:
    """
    Fetch the user's current live LinkedIn profile from LinkedIn's API.
    Use this when the user asks to improve their profile, wants it analyzed,
    or needs profile-specific advice.
    """
    user_id = state["user_id"]
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return "User not found."
        client = LinkedInClient(user.access_token)
        profile = await client.get_profile()
        return str(profile)
    finally:
        db.close()


@tool
async def analyze_profile(
    state: Annotated[dict, InjectedState],
) -> str:
    """
    Audit the user's LinkedIn profile against their career goals and return a
    prioritized, section-by-section improvement plan with specific rewrites.
    Use this when the user asks to audit, review, or improve their LinkedIn profile.
    This tool automatically fetches their stored profile — no need to ask them to paste anything.
    """
    user_id = state["user_id"]
    db: Session = SessionLocal()
    try:
        memory = get_all_memory(db, user_id)
        stored_profile = get_linkedin_profile_data(db, user_id)

        if not stored_profile or not stored_profile.headline:
            return (
                "I don't have your LinkedIn profile stored yet. "
                "Go to the Profile page in the app, fill in your headline, about section, "
                "experience, and skills, then come back and I'll run the full audit."
            )

        profile_sections = f"""
Headline: {stored_profile.headline}

About:
{stored_profile.about}

Experience:
{stored_profile.experience}

Skills: {stored_profile.skills}
""".strip()

        profile_best_practices = query_documents(KNOWLEDGE_COLLECTION, "LinkedIn profile optimization headline about section", n_results=4)
        best_practices_str = "\n\n".join(profile_best_practices) if profile_best_practices else ""

        memory_str = ""
        if memory:
            memory_str = "\n".join(f"- {k}: {v}" for k, v in memory.items())

        system = SystemMessage(content=f"""You are a senior LinkedIn profile coach specializing in tech and AI/ML engineers.

Your job: audit this engineer's LinkedIn profile and return a concrete, prioritized improvement plan.

## What You Know About This User
{memory_str if memory_str else "No prior context stored yet."}

## LinkedIn Profile Best Practices (from knowledge base)
{best_practices_str}

## How to structure your audit

Return exactly this format:

**Target Role:** [infer from memory, or note if unknown]

---

### Priority 1 — Fix These First (Highest Impact)
For each item: state the problem clearly, then give the exact rewrite or specific fix.

### Priority 2 — Important Improvements
Same format — problem + specific fix or example.

### Priority 3 — Quick Wins
Small changes that take under 5 minutes.

---

**Your single most important next action:** [one sentence]

## Rules
- Be specific. If their headline is weak, write a better one. Don't say "improve your headline."
- Compare everything against their target role and career goals from memory.
- Flag any keywords missing for their target role.
- If a section wasn't shared, note what's likely missing and why it matters.
- No corporate language. No "great job on X." Just the gaps and the fixes.
""")

        response = coach_llm.invoke([
            system,
            HumanMessage(content=f"Here is my LinkedIn profile content:\n\n{profile_sections}"),
        ])

        return response.content

    finally:
        db.close()
