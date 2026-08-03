from src.core.tools.time_tool import CurrentTimeTool
from src.core.tools.search_tool import SearchWebTool
from src.core.tools.n8n_tool import N8nTool
from src.core.tools.image_tool import ImageProcessingTool
from config import settings
import logging

time_tool = CurrentTimeTool()
search_tool = SearchWebTool()
n8n_tool = N8nTool(webhook_url=settings.n8n_webhook_url)
image_tool = ImageProcessingTool(line_access_token=settings.line_channel_access_token)

# Initialize the agent
agent = Agent(
    name="LineOrchestratorAgent",
    model="gemini-2.5-flash",
    tools=[time_tool, search_tool, n8n_tool, image_tool],
    instruction="You are a helpful AI assistant. Use tools when necessary. When a user uploads an image, use the process_image tool with the provided message_id to analyze it.",
)

def process_message(user_id: str, text: str) -> str:
    # Context or user_id can be used here if needed
    try:
        return agent.run(text)
    except Exception as e:
        logger.error(f"Error in process_message: {e}")
        return "I am currently experiencing technical difficulties. Please try again later."