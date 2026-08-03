from typing import Any, Dict
from src.core.tool import BaseTool

class SearchWebTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_web"

    @property
    def description(self) -> str:
        return "Searches the web for the given query."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str, **kwargs) -> Any:
        return f"Search results for: {query}"