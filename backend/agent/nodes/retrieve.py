from backend.agent.state import AgentState
from backend.rag.vector_store import (
    KNOWLEDGE_COLLECTION,
    LINKEDIN_EXAMPLES_COLLECTION,
    USER_POSTS_COLLECTION,
    USER_PROFILE_COLLECTION,
    query_documents,
)


def retrieve_node(state: AgentState) -> dict:
    """
    First node in the graph. Runs before Claude sees anything.
    Finds the most relevant chunks from Pinecone based on the user's message
    and injects them into state so Claude can use them.
    """
    messages = state["messages"]
    if not messages:
        return {"retrieved_context": []}

    last_message = messages[-1]
    query = last_message.content if hasattr(last_message, "content") else str(last_message)

    kb_results = query_documents(KNOWLEDGE_COLLECTION, query, n_results=3)
    post_results = query_documents(USER_POSTS_COLLECTION, query, n_results=2)
    profile_results = query_documents(USER_PROFILE_COLLECTION, query, n_results=2)
    example_results = query_documents(LINKEDIN_EXAMPLES_COLLECTION, query, n_results=3)

    return {"retrieved_context": kb_results + post_results + profile_results + example_results}
