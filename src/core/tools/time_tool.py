from typing import Any, Dict
import datetime
from src.core.tool import BaseTool

class CurrentTimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "Returns the current date and time."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }

    def execute(self, **kwargs) -> Any:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
