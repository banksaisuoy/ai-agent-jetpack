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

                {"title": f"Result 1 for {query}", "url": "http://example.com/1"},
                {"title": f"Result 2 for {query}", "url": "http://example.com/2"}
            ]
        }