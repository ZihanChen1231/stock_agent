from __future__ import annotations

from collections.abc import Iterable

from app.core.config import Settings
from app.tools.base import BaseTool
from app.tools.cnbc_news_client import CNBCNewsClient
from app.tools.market_data import StockNewsHistoryTool, StockNewsTool, StockPriceHistoryTool, StockPriceTool
from app.tools.price_history_client import PriceHistoryClient
from app.tools.ycnbc_client import YCNBCClient


class ToolRegistry:
    def __init__(self, tools: Iterable[BaseTool]) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._canonical_tools: list[BaseTool] = []
        for tool in tools:
            self._canonical_tools.append(tool)
            self._tools[tool.name] = tool
            for alias in tool.aliases:
                self._tools[alias] = tool

    @classmethod
    def from_settings(cls, settings: Settings) -> "ToolRegistry":
        ycnbc_client = YCNBCClient()
        cnbc_news_client = CNBCNewsClient()
        price_history_client = PriceHistoryClient()
        return cls(
            tools=[
                StockPriceTool(mode=settings.tool_mode, ycnbc_client=ycnbc_client),
                StockNewsTool(mode=settings.tool_mode, news_client=cnbc_news_client),
                StockPriceHistoryTool(mode=settings.tool_mode, history_client=price_history_client),
                StockNewsHistoryTool(mode=settings.tool_mode, news_client=cnbc_news_client),
            ]
        )

    def get(self, name: str) -> BaseTool:
        return self._tools[name]

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def all(self) -> list[BaseTool]:
        return list(self._canonical_tools)
