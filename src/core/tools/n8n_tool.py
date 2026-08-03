from typing import Any, Dict
import httpx
import logging
from src.core.tool import BaseTool

logger = logging.getLogger(__name__)

class N8nTool(BaseTool):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    @property
    def name(self) -> str:
        return "trigger_n8n_workflow"

    @property
    def description(self) -> str:
        return "Triggers an n8n workflow using the webhook URL."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Data to pass to the workflow"
                }
            },
            "required": ["data"]
        }

    def execute(self, data: str, **kwargs) -> Any:
        if not self.webhook_url:
            return "N8N webhook URL is not configured."
        
        try:
            response = httpx.post(self.webhook_url, json={"data": data})
            response.raise_for_status()
            return "Workflow triggered successfully."
        except Exception as e:
            logger.error(f"Error triggering n8n workflow: {e}")
            return f"Failed to trigger workflow: {e}"