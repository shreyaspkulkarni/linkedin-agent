from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph

from backend.agent.nodes.agent import agent_node
from backend.agent.nodes.retrieve import retrieve_node
from backend.agent.nodes.tools import tools_node
from backend.agent.state import AgentState


def should_continue(state: AgentState) -> str:
    """
    Routing function — decides what happens after the agent node runs.

    If Claude's response contains tool_calls → go to tools node
    If Claude's response is a plain message → we're done, go to END
    """
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


def build_graph():
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node)

    # Define the flow
    graph.add_edge(START, "retrieve")       # always start with RAG
    graph.add_edge("retrieve", "agent")     # then Claude reasons

    # After agent: either call tools or end
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})

    # After tools: always go back to agent so Claude can reason about the results
    graph.add_edge("tools", "agent")

    return graph.compile()


# Single compiled graph instance reused across requests
agent_graph = build_graph()
