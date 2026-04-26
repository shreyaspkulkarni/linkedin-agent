from fastapi import APIRouter, Depends, HTTPException
from jose import JWTError, jwt
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.agent.graph import agent_graph
from backend.config import settings
from backend.db.crud import get_all_memory
from backend.db.database import get_db
from backend.db.models import Conversation, User

router = APIRouter(prefix="/agent", tags=["agent"])
ALGORITHM = "HS256"


class ChatRequest(BaseModel):
    token: str
    message: str


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


@router.post("/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message to the LinkedIn AI agent and get a response."""
    user = get_current_user(request.token, db)

    # Load user's memory from PostgreSQL to seed the agent state
    memory = get_all_memory(db, user.id)

    # Load last 10 conversation turns from DB so agent has context
    history = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .limit(10)
        .all()
    )
    history_messages = []
    for turn in reversed(history):
        if turn.role == "user":
            history_messages.append(HumanMessage(content=turn.content))
        else:
            history_messages.append(AIMessage(content=turn.content))

    # Build initial state — history + current message
    initial_state = {
        "messages": history_messages + [HumanMessage(content=request.message)],
        "user_id": str(user.id),
        "memory": memory,
        "retrieved_context": [],
    }

    # Run the graph — this is the full agent loop
    result = await agent_graph.ainvoke(initial_state)

    # Extract the final response
    final_message = result["messages"][-1]
    response_text = final_message.content if hasattr(final_message, "content") else str(final_message)

    # Persist conversation to DB
    db.add(Conversation(user_id=user.id, role="user", content=request.message))
    db.add(Conversation(user_id=user.id, role="assistant", content=response_text))
    db.commit()

    return {"response": response_text, "user_id": str(user.id)}


@router.delete("/conversations")
def clear_conversations(token: str, db: Session = Depends(get_db)):
    """Clear the user's conversation history so the agent starts fresh."""
    user = get_current_user(token, db)
    db.query(Conversation).filter(Conversation.user_id == user.id).delete()
    db.commit()
    return {"message": "Conversation history cleared."}
