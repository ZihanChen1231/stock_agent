from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError
