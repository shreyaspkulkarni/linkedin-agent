from typing import Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # add_messages is a special reducer — instead of overwriting,
    # it appends new messages to the existing list.
    # This is how the agent keeps the full conversation history.
    messages: Annotated[list[BaseMessage], add_messages]

    # Who is talking to the agent
    user_id: str

    # Loaded from PostgreSQL at start — career goals, preferences, writing style
    memory: dict

    # What RAG retrieved for the current query
    retrieved_context: list[str]
