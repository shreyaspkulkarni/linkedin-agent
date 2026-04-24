from typing import Annotated

from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy.orm import Session

from backend.db.crud import get_all_memory, set_memory
from backend.db.database import SessionLocal


@tool
def save_memory(
    key: str,
    value: str,
    state: Annotated[dict, InjectedState],
) -> str:
    """
    Save something important the user told you to persistent memory.
    Use this when the user shares their career goals, target role, preferred topics,
    or writing style preferences — anything you should remember across sessions.

    Args:
        key: what you're remembering (e.g. 'career_goals', 'target_role', 'topics')
        value: the value to store
    """
    user_id = state["user_id"]
    db: Session = SessionLocal()
    try:
        set_memory(db, user_id, key, value)
        return f"Saved: {key} = {value}"
    finally:
        db.close()


@tool
def get_memory(state: Annotated[dict, InjectedState]) -> str:
    """
    Retrieve everything stored in memory for this user.
    Call this to load their goals and preferences before giving advice.
    """
    user_id = state["user_id"]
    db: Session = SessionLocal()
    try:
        memory = get_all_memory(db, user_id)
        if not memory:
            return "No memory yet. Ask the user about their career goals and what they want on LinkedIn."
        return str(memory)
    finally:
        db.close()
