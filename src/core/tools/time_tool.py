from src.core.tool import BaseTool

class CurrentTimeTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_current_time"


    @property
    def description(self) -> str: