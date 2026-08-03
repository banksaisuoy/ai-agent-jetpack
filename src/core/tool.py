from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does."""
        pass
    
    @property
    def parameters(self) -> Dict[str, Any]:
        """A JSON schema defining the parameters for the tool."""
        return {
            "type": "object",
            "properties": {},
        }

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Executes the tool with the given parameters."""
        pass