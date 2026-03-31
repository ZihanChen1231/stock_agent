from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str
    description: str
    aliases: list[str] = []
    parameters_schema: dict[str, Any] = {"type": "object", "properties": {}}

    @abstractmethod
    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def mcp_spec(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.parameters_schema,
        }
