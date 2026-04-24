from langchain_core.tools import tool
from tavily import TavilyClient

from backend.config import settings


@tool
def search_trends(query: str) -> str:
    """
    Search the web for trending topics, news, and discussions relevant to the query.
    Use this when the user asks what to post about this week, wants post ideas based
    on current trends, or asks what's happening in a specific tech space right now.

    Args:
        query: what to search for, e.g. "trending GenAI topics for software engineers LinkedIn"
    """
    client = TavilyClient(api_key=settings.tavily_api_key)

    results = client.search(
        query=query,
        search_depth="basic",
        max_results=5,
        include_answer=True,
    )

    # Format results cleanly for Claude to reason over
    output = []

    if results.get("answer"):
        output.append(f"Summary: {results['answer']}\n")

    for r in results.get("results", []):
        output.append(f"- {r['title']}: {r['content'][:200]}...")

    return "\n".join(output) if output else "No results found."
