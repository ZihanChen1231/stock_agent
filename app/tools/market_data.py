from __future__ import annotations

from typing import Any
from typing import Optional

from app.tools.base import BaseTool
from app.tools.cnbc_news_client import CNBCNewsClient
from app.tools.price_history_client import PriceHistoryClient
from app.tools.ycnbc_client import YCNBCClient


class StockPriceTool(BaseTool):
    name = "get_stock_price"
    aliases = ["stock_price"]
    description = "Get the latest stock price snapshot for a ticker."
    parameters_schema = {
        "type": "object",
        "title": "GetStockPriceInput",
        "properties": {
            "ticker": {
                "type": "string",
                "title": "Ticker",
                "description": "Ticker symbol like AAPL.",
                "examples": ["AAPL", "MSFT", "NVDA"],
            },
        },
        "required": ["ticker"],
        "additionalProperties": False,
        "examples": [
            {"ticker": "AAPL"},
            {"ticker": "MSFT"},
        ],
    }

    def __init__(self, mode: str = "mock", ycnbc_client: Optional[YCNBCClient] = None) -> None:
        self.mode = mode
        self.ycnbc_client = ycnbc_client or YCNBCClient()

    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticker = arguments["ticker"].upper()
        if self.mode == "mock" or not self.ycnbc_client.is_available():
            return self._mock_response(ticker)

        try:
            return await self.ycnbc_client.quote_summary(ticker)
        except Exception as exc:
            fallback = self._mock_response(ticker)
            fallback["warning"] = "ycnbc quote fetch failed; using mock response."
            fallback["error"] = str(exc)
            return fallback

    def _mock_response(self, ticker: str) -> dict[str, Any]:
        seed = sum(ord(char) for char in ticker)
        price = round(80 + (seed % 140) + ((seed % 13) / 10), 2)
        day_change = round(((seed % 11) - 5) * 0.72, 2)
        previous_close = round(price - day_change, 2)
        change_pct = round((day_change / previous_close) * 100, 2) if previous_close else 0.0
        return {
            "ticker": ticker,
            "current_price": price,
            "day_change": day_change,
            "day_change_percent": change_pct,
            "high": round(price * 1.01, 2),
            "low": round(price * 0.99, 2),
            "open": round(previous_close * 1.002, 2),
            "previous_close": previous_close,
            "source": "mock",
        }


class StockNewsTool(BaseTool):
    name = "get_stock_news"
    aliases = ["stock_news"]
    description = "Get recent CNBC news headlines for a stock ticker."
    parameters_schema = {
        "type": "object",
        "title": "GetStockNewsInput",
        "properties": {
            "ticker": {
                "type": "string",
                "title": "Ticker",
                "description": "Ticker symbol like AAPL.",
                "examples": ["AAPL", "TSLA", "AMZN"],
            },
            "company_name": {
                "type": "string",
                "title": "Company Name",
                "description": "Optional company name like Apple.",
                "examples": ["Apple", "Tesla", "Amazon"],
            },
            "max_items": {
                "type": "integer",
                "title": "Max Items",
                "description": "Maximum number of news items to return.",
                "default": 5,
                "minimum": 1,
                "maximum": 10,
                "examples": [3, 5],
            },
        },
        "required": ["ticker"],
        "additionalProperties": False,
        "examples": [
            {"ticker": "AAPL", "company_name": "Apple", "max_items": 3},
            {"ticker": "TSLA", "max_items": 5},
        ],
    }

    def __init__(self, mode: str = "mock", news_client: Optional[CNBCNewsClient] = None) -> None:
        self.mode = mode
        self.news_client = news_client or CNBCNewsClient()

    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticker = arguments["ticker"].upper()
        company_name = arguments.get("company_name") or ticker
        max_items = int(arguments.get("max_items", 5))
        if self.mode == "mock":
            return self._mock_response(ticker, company_name)

        try:
            articles = await self.news_client.fetch_stock_news(
                ticker=ticker,
                company_name=company_name,
                max_items=max_items,
            )
            return {
                "ticker": ticker,
                "articles": articles,
                "source": "cnbc_direct",
            }
        except Exception as exc:
            fallback = self._mock_response(ticker, company_name)
            fallback["warning"] = "Direct CNBC news fetch failed; using mock response."
            fallback["error"] = str(exc)
            return fallback

    def _mock_response(self, ticker: str, company_name: str) -> dict[str, Any]:
        headlines = [
            f"{company_name} expands product roadmap focus in a competitive market.",
            f"Analysts debate near-term catalysts for {ticker} ahead of the next earnings cycle.",
            f"{company_name} faces a mixed macro backdrop with margin discipline in focus.",
        ]
        return {
            "ticker": ticker,
            "articles": [
                {
                    "title": headline,
                    "source": "mock_feed",
                    "url": None,
                    "published_at": None,
                }
                for headline in headlines
            ],
            "source": "mock",
        }


class StockPriceHistoryTool(BaseTool):
    name = "get_stock_price_history"
    aliases = ["stock_price_history"]
    description = "Get daily stock price history over the past N days."
    parameters_schema = {
        "type": "object",
        "title": "GetStockPriceHistoryInput",
        "properties": {
            "ticker": {
                "type": "string",
                "title": "Ticker",
                "description": "Ticker symbol like AAPL.",
                "examples": ["AAPL", "MSFT"],
            },
            "past_days": {
                "type": "integer",
                "title": "Past Days",
                "description": "Trailing day window for historical prices.",
                "default": 7,
                "minimum": 1,
                "maximum": 365,
                "examples": [7, 30],
            },
        },
        "required": ["ticker"],
        "additionalProperties": False,
        "examples": [{"ticker": "AAPL", "past_days": 30}],
    }

    def __init__(self, mode: str = "mock", history_client: Optional[PriceHistoryClient] = None) -> None:
        self.mode = mode
        self.history_client = history_client or PriceHistoryClient()

    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticker = arguments["ticker"].upper()
        past_days = int(arguments.get("past_days", 7))
        if self.mode == "mock":
            return self._mock_response(ticker, past_days)

        try:
            return await self.history_client.fetch_daily_history(ticker=ticker, past_days=past_days)
        except Exception as exc:
            fallback = self._mock_response(ticker, past_days)
            fallback["warning"] = "Historical price fetch failed; using mock response."
            fallback["error"] = str(exc)
            return fallback

    def _mock_response(self, ticker: str, past_days: int) -> dict[str, Any]:
        seed = sum(ord(char) for char in ticker)
        start_price = 80 + (seed % 120)
        bars = []
        for index in range(past_days):
            close = round(start_price + index * 0.6 + ((seed + index) % 5) * 0.2, 2)
            bars.append(
                {
                    "trading_date": f"2026-03-{max(1, 31 - past_days + index):02d}",
                    "open": round(close - 0.5, 2),
                    "high": round(close + 1.2, 2),
                    "low": round(close - 1.0, 2),
                    "close": close,
                    "volume": float(1000000 + index * 5000),
                }
            )
        start_close = bars[0]["close"] if bars else None
        end_close = bars[-1]["close"] if bars else None
        return_percent = round(((end_close - start_close) / start_close) * 100, 2) if start_close and end_close else None
        return {
            "ticker": ticker,
            "past_days": past_days,
            "bars": bars,
            "summary": {
                "start_close": start_close,
                "end_close": end_close,
                "return_percent": return_percent,
                "average_volume": round(sum(bar["volume"] for bar in bars) / len(bars), 2) if bars else None,
                "bars": len(bars),
            },
            "source": "mock",
        }


class StockNewsHistoryTool(BaseTool):
    name = "get_stock_news_history"
    aliases = ["stock_news_history"]
    description = "Get recent dated stock news over the past N days."
    parameters_schema = {
        "type": "object",
        "title": "GetStockNewsHistoryInput",
        "properties": {
            "ticker": {
                "type": "string",
                "title": "Ticker",
                "description": "Ticker symbol like AAPL.",
                "examples": ["AAPL", "TSLA"],
            },
            "company_name": {
                "type": "string",
                "title": "Company Name",
                "description": "Optional company name like Apple.",
                "examples": ["Apple", "Tesla"],
            },
            "past_days": {
                "type": "integer",
                "title": "Past Days",
                "description": "Trailing day window for news.",
                "default": 7,
                "minimum": 1,
                "maximum": 90,
                "examples": [7, 14],
            },
            "max_items": {
                "type": "integer",
                "title": "Max Items",
                "description": "Maximum number of news items to return.",
                "default": 10,
                "minimum": 1,
                "maximum": 20,
                "examples": [5, 10],
            },
        },
        "required": ["ticker"],
        "additionalProperties": False,
        "examples": [{"ticker": "AAPL", "company_name": "Apple", "past_days": 7, "max_items": 5}],
    }

    def __init__(self, mode: str = "mock", news_client: Optional[CNBCNewsClient] = None) -> None:
        self.mode = mode
        self.news_client = news_client or CNBCNewsClient()

    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticker = arguments["ticker"].upper()
        company_name = arguments.get("company_name") or ticker
        past_days = int(arguments.get("past_days", 7))
        max_items = int(arguments.get("max_items", 10))
        if self.mode == "mock":
            return self._mock_response(ticker, company_name, past_days, max_items)

        try:
            return await self.news_client.fetch_stock_news_history(
                ticker=ticker,
                company_name=company_name,
                past_days=past_days,
                max_items=max_items,
            )
        except Exception as exc:
            fallback = self._mock_response(ticker, company_name, past_days, max_items)
            fallback["warning"] = "Historical news fetch failed; using mock response."
            fallback["error"] = str(exc)
            return fallback

    def _mock_response(self, ticker: str, company_name: str, past_days: int, max_items: int) -> dict[str, Any]:
        articles = [
            {
                "title": f"{company_name} headline {index + 1} within trailing window",
                "summary": f"Mock recent catalyst for {ticker} over the last {past_days} days.",
                "source": "mock_feed",
                "url": None,
                "published_at": f"2026-03-{max(1, 31 - index):02d}T12:00:00Z",
            }
            for index in range(min(max_items, 5))
        ]
        return {
            "ticker": ticker,
            "past_days": past_days,
            "articles": articles,
            "article_count": len(articles),
            "source": "mock",
        }
