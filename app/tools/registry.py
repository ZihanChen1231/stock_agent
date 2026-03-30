from __future__ import annotations

from collections.abc import Iterable

from app.core.config import Settings
from app.tools.base import BaseTool
from app.tools.market_data import StockNewsTool, StockPriceTool


class ToolRegistry:
    def __init__(self, tools: Iterable[BaseTool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    @classmethod
    def from_settings(cls, settings: Settings) -> "ToolRegistry":
        return cls(
            tools=[
                StockPriceTool(mode=settings.tool_mode, finnhub_api_key=settings.finnhub_api_key),
                StockNewsTool(mode=settings.tool_mode, news_api_key=settings.news_api_key),
            ]
        )

    def get(self, name: str) -> BaseTool:
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools.keys())
