from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.state import AgentState
from backend.agent.tools.content_tools import draft_post, get_my_posts
from backend.agent.tools.linkedin_tools import analyze_profile, get_linkedin_profile
from backend.agent.tools.memory_tools import get_memory, save_memory
from backend.agent.tools.search_tools import search_trends
from backend.config import settings

llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.7,
)

# publish_post and schedule_post are NOT agent tools — user triggers those from the frontend
ALL_TOOLS = [get_memory, save_memory, get_linkedin_profile, analyze_profile, draft_post, get_my_posts, search_trends]

# Bind tools to the model — Claude now knows these tools exist and can call them
llm_with_tools = llm.bind_tools(ALL_TOOLS)


def agent_node(state: AgentState) -> dict:
    """
    The brain. Claude reads the full state and either:
    - Calls one or more tools (returns tool_calls in its message)
    - Gives a final answer (returns content in its message)
    """
    retrieved_context = state.get("retrieved_context", [])
    memory = state.get("memory", {})

    # Build a system message that includes RAG context and memory
    context_block = ""
    if retrieved_context:
        context_block = "\n\n## Relevant Knowledge\n" + "\n---\n".join(retrieved_context)

    memory_block = ""
    if memory:
        memory_block = f"\n\n## What You Know About This User\n{memory}"

    system = SystemMessage(content=SYSTEM_PROMPT + context_block + memory_block)

    response = llm_with_tools.invoke([system] + state["messages"])
    return {"messages": [response]}
