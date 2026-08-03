from typing import Any, Dict
import datetime
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo
from src.core.tool import BaseTool

class CurrentTimeTool(BaseTool):

    @property
    def description(self) -> str:
        return "Returns the current date and time in ISO format."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "The timezone to get the current time for (e.g. 'UTC', 'America/New_York'). Default is UTC."
                }
            }
        }

    def execute(self, timezone: str = "UTC", **kwargs) -> Any:
        try:
            tz = zoneinfo.ZoneInfo(timezone)
        except Exception:
            tz = datetime.timezone.utc
            
        return datetime.datetime.now(tz).isoformat()