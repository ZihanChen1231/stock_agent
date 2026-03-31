from __future__ import annotations

import asyncio
from typing import Any
from typing import Optional


class YCNBCClient:
    def __init__(self) -> None:
        self._ycnbc = None

    def is_available(self) -> bool:
        try:
            self._load_module()
        except ImportError:
            return False
        return True

    async def quote_summary(self, ticker: str) -> dict[str, Any]:
        return await asyncio.to_thread(self._quote_summary_sync, ticker)

    async def latest_news(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        max_items: int = 5,
        category: str = "latest",
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(
            self._latest_news_sync,
            ticker,
            company_name,
            max_items,
            category,
        )

    def _quote_summary_sync(self, ticker: str) -> dict[str, Any]:
        module = self._load_module()
        markets = module.Markets()
        payload = markets.quote_summary(ticker)
        return normalize_quote_summary(ticker=ticker, payload=payload)

    def _latest_news_sync(
        self,
        ticker: str,
        company_name: Optional[str],
        max_items: int,
        category: str,
    ) -> list[dict[str, Any]]:
        module = self._load_module()
        news_client = module.News()
        getter = getattr(news_client, category, None)
        if getter is None or not callable(getter):
            getter = news_client.latest

        payload = getter()
        return normalize_news_items(
            ticker=ticker,
            company_name=company_name,
            payload=payload,
            max_items=max_items,
        )

    def _load_module(self):  # type: ignore[no-untyped-def]
        if self._ycnbc is None:
            import ycnbc  # type: ignore

            self._ycnbc = ycnbc
        return self._ycnbc


def normalize_quote_summary(ticker: str, payload: Any) -> dict[str, Any]:
    source = "ycnbc"
    raw = payload if isinstance(payload, dict) else {"raw": payload}

    price = first_value(
        raw,
        [
            "last",
            "lastPrice",
            "price",
            "currentPrice",
            "close",
        ],
    )
    previous_close = first_value(raw, ["previousClose", "prevClose", "priorClose", "closePrev"])
    open_price = first_value(raw, ["open", "openPrice"])
    high = first_value(raw, ["high", "dayHigh"])
    low = first_value(raw, ["low", "dayLow"])
    day_change = first_value(raw, ["change", "changeValue", "netChange"])
    change_percent = first_value(raw, ["change_pct", "changePercent", "percentChange", "pctChange"])

    return {
        "ticker": ticker.upper(),
        "current_price": to_number(price),
        "day_change": to_number(day_change),
        "day_change_percent": to_number(change_percent),
        "high": to_number(high),
        "low": to_number(low),
        "open": to_number(open_price),
        "previous_close": to_number(previous_close),
        "source": source,
        "raw": raw,
    }


def normalize_news_items(
    ticker: str,
    company_name: Optional[str],
    payload: Any,
    max_items: int,
) -> list[dict[str, Any]]:
    items = payload if isinstance(payload, list) else payload.get("data", []) if isinstance(payload, dict) else []
    normalized: list[dict[str, Any]] = []
    ticker_upper = ticker.upper()
    company = (company_name or "").strip().lower()

    for item in items:
        if not isinstance(item, dict):
            continue

        title = stringify(first_value(item, ["title", "headline", "name"]))
        summary = stringify(first_value(item, ["description", "summary", "deck"]))
        url = stringify(first_value(item, ["url", "link", "cnbc_url"]))
        published_at = stringify(first_value(item, ["publishedAt", "datePublished", "pubDate", "date"]))
        source = stringify(first_value(item, ["source", "publisher"])) or "CNBC"

        haystack = " ".join([title, summary, url]).lower()
        if company or ticker_upper:
            if ticker_upper.lower() not in haystack and company and company not in haystack:
                continue

        normalized.append(
            {
                "title": title,
                "summary": summary,
                "source": source,
                "url": url or None,
                "published_at": published_at or None,
            }
        )
        if len(normalized) >= max_items:
            break

    if normalized:
        return normalized

    fallback = []
    for item in items[:max_items]:
        if not isinstance(item, dict):
            continue
        fallback.append(
            {
                "title": stringify(first_value(item, ["title", "headline", "name"])) or "Untitled CNBC item",
                "summary": stringify(first_value(item, ["description", "summary", "deck"])),
                "source": stringify(first_value(item, ["source", "publisher"])) or "CNBC",
                "url": stringify(first_value(item, ["url", "link", "cnbc_url"])) or None,
                "published_at": stringify(first_value(item, ["publishedAt", "datePublished", "pubDate", "date"])) or None,
            }
        )
    return fallback


def first_value(payload: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def to_number(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).replace("%", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None
