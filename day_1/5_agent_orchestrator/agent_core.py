from src.core.agent import Agent
from src.core.tools.time_tool import CurrentTimeTool
from src.core.tools.search_tool import SearchWebTool
from src.core.tools.n8n_tool import N8nTool
from config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize the tools
time_tool = CurrentTimeTool()
search_tool = SearchWebTool()
n8n_tool = N8nTool(webhook_url=settings.n8n_webhook_url)

# Initialize the agent
agent = Agent(
    name="LineOrchestratorAgent",
    model="gemini-2.5-flash",
    tools=[time_tool, search_tool, n8n_tool],
    instruction="You are a helpful AI assistant. Use tools when necessary.",
)
