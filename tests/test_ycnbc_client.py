from app.tools.ycnbc_client import normalize_news_items
from app.tools.ycnbc_client import normalize_quote_summary


def test_normalize_quote_summary_maps_common_fields() -> None:
    payload = {
        "last": "188.52",
        "change": "-1.48",
        "changePercent": "-0.78%",
        "high": "190.00",
        "low": "187.30",
        "open": "189.50",
        "previousClose": "190.00",
    }

    result = normalize_quote_summary("AAPL", payload)

    assert result["ticker"] == "AAPL"
    assert result["current_price"] == 188.52
    assert result["day_change"] == -1.48
    assert result["day_change_percent"] == -0.78
    assert result["previous_close"] == 190.0
    assert result["source"] == "ycnbc"


def test_normalize_news_items_filters_for_ticker_or_company() -> None:
    payload = [
        {
            "title": "Apple unveils new AI features for the iPhone",
            "description": "AAPL investors are watching the launch closely.",
            "url": "https://www.cnbc.com/apple-ai",
            "publishedAt": "2026-03-30T12:00:00Z",
            "source": "CNBC",
        },
        {
            "title": "Oil prices rise on supply concerns",
            "description": "Energy traders monitor the next OPEC signal.",
            "url": "https://www.cnbc.com/oil",
            "publishedAt": "2026-03-30T10:00:00Z",
            "source": "CNBC",
        },
    ]

    result = normalize_news_items("AAPL", "Apple", payload, max_items=5)

    assert len(result) == 1
    assert "Apple" in result[0]["title"]
