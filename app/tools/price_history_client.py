from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from datetime import datetime
from datetime import timedelta
from io import StringIO
from typing import Any

import httpx


STOOQ_DAILY_URL = "https://stooq.com/q/d/l/"


@dataclass
class PriceBar:
    trading_date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class PriceHistoryClient:
    async def fetch_daily_history(self, ticker: str, past_days: int) -> dict[str, Any]:
        symbol = normalize_stooq_symbol(ticker)
        params = {"s": symbol, "i": "d"}
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(STOOQ_DAILY_URL, params=params)
            response.raise_for_status()

        bars = parse_stooq_csv(response.text)
        cutoff = date.today() - timedelta(days=past_days)
        filtered = [bar for bar in bars if parse_date(bar.trading_date) >= cutoff]
        if not filtered:
            filtered = bars[-past_days:] if bars else []

        return {
            "ticker": ticker.upper(),
            "past_days": past_days,
            "bars": [bar.__dict__ for bar in filtered],
            "summary": summarize_bars(filtered),
            "source": "stooq",
        }


def normalize_stooq_symbol(ticker: str) -> str:
    normalized = ticker.strip().lower()
    if "." in normalized:
        return normalized
    return f"{normalized}.us"


def parse_stooq_csv(raw: str) -> list[PriceBar]:
    reader = csv.DictReader(StringIO(raw))
    bars: list[PriceBar] = []
    for row in reader:
        if not row.get("Date") or row.get("Close") in (None, "", "N/D"):
            continue
        bars.append(
            PriceBar(
                trading_date=row["Date"],
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]) if row.get("Volume") not in (None, "", "N/D") else 0.0,
            )
        )
    return bars


def summarize_bars(bars: list[PriceBar]) -> dict[str, Any]:
    if not bars:
        return {"start_close": None, "end_close": None, "return_percent": None, "average_volume": None}

    start_close = bars[0].close
    end_close = bars[-1].close
    return_percent = ((end_close - start_close) / start_close * 100.0) if start_close else None
    average_volume = sum(bar.volume for bar in bars) / len(bars) if bars else None
    return {
        "start_close": start_close,
        "end_close": end_close,
        "return_percent": round(return_percent, 2) if return_percent is not None else None,
        "average_volume": round(average_volume, 2) if average_volume is not None else None,
        "bars": len(bars),
    }


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
