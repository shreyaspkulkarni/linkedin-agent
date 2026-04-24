from langgraph.prebuilt import ToolNode

from backend.agent.tools.content_tools import draft_post, get_my_posts
from backend.agent.tools.linkedin_tools import analyze_profile, get_linkedin_profile
from backend.agent.tools.memory_tools import get_memory, save_memory
from backend.agent.tools.search_tools import search_trends

# publish_post and schedule_post are user-controlled API endpoints, not agent tools
tools_node = ToolNode(tools=[get_memory, save_memory, get_linkedin_profile, analyze_profile, draft_post, get_my_posts, search_trends])
