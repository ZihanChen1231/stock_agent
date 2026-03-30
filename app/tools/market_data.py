from __future__ import annotations

from typing import Any
from typing import Optional

import httpx

from app.tools.base import BaseTool


class StockPriceTool(BaseTool):
    name = "stock_price"
    description = "Fetches a stock price snapshot and simple daily move metrics."

    def __init__(self, mode: str = "mock", finnhub_api_key: Optional[str] = None) -> None:
        self.mode = mode
        self.finnhub_api_key = finnhub_api_key

    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticker = arguments["ticker"].upper()
        if self.mode != "live" or not self.finnhub_api_key:
            return self._mock_response(ticker)

        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": ticker, "token": self.finnhub_api_key}
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        return {
            "ticker": ticker,
            "current_price": payload.get("c"),
            "day_change": payload.get("d"),
            "day_change_percent": payload.get("dp"),
            "high": payload.get("h"),
            "low": payload.get("l"),
            "open": payload.get("o"),
            "previous_close": payload.get("pc"),
            "source": "finnhub",
        }

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
    name = "stock_news"
    description = "Returns recent news headlines or mock catalysts for a stock."

    def __init__(self, mode: str = "mock", news_api_key: Optional[str] = None) -> None:
        self.mode = mode
        self.news_api_key = news_api_key

    async def invoke(self, arguments: dict[str, Any]) -> dict[str, Any]:
        ticker = arguments["ticker"].upper()
        company_name = arguments.get("company_name") or ticker
        if self.mode != "live" or not self.news_api_key:
            return self._mock_response(ticker, company_name)

        query = f"{company_name} OR {ticker}"
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "pageSize": 5,
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": self.news_api_key,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        articles = [
            {
                "title": article.get("title"),
                "source": (article.get("source") or {}).get("name"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
            }
            for article in payload.get("articles", [])[:5]
        ]
        return {"ticker": ticker, "articles": articles, "source": "newsapi"}

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
