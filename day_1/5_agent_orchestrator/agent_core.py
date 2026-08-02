from google.adk.agents import LlmAgent
from config import settings
import datetime
import httpx
import logging

logger = logging.getLogger(__name__)

def get_current_time() -> str:
    """Returns the current date and time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def search_web(query: str) -> str:
    """Searches the web for the given query. (Mock)"""
    return f"Search results for: {query}"

def trigger_n8n_workflow(data: str) -> str:
    """Triggers an n8n workflow using the webhook URL from environment variables."""
    if not settings.n8n_webhook_url:
        return "N8N webhook URL is not configured."
    
    try:
        response = httpx.post(settings.n8n_webhook_url, json={"data": data})
        response.raise_for_status()
        return "Workflow triggered successfully."
    except Exception as e:
        logger.error(f"Error triggering n8n workflow: {e}")
        return f"Failed to trigger workflow: {e}"

# Initialize the agent
agent = LlmAgent(
    name="LineOrchestratorAgent",
    model="gemini-2.5-flash",
    tools=[get_current_time, search_web, trigger_n8n_workflow],
    instruction="You are a helpful AI assistant. Use tools when necessary.",
)

def process_message(user_id: str, text: str) -> str:
    """Runs the ADK agent and returns the final response."""
    try:
        response = agent.run(text)
        return response
    except Exception as e:
        logger.error(f"Error running agent: {e}")
        return f"Sorry, I encountered an error: {e}"