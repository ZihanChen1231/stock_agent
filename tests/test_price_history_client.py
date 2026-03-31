from app.tools.price_history_client import normalize_stooq_symbol
from app.tools.price_history_client import parse_stooq_csv
from app.tools.price_history_client import summarize_bars


def test_normalize_stooq_symbol_for_us_stock() -> None:
    assert normalize_stooq_symbol("AAPL") == "aapl.us"


def test_parse_stooq_csv_and_summary() -> None:
    raw = "Date,Open,High,Low,Close,Volume\n2026-03-28,100,102,99,101,1000\n2026-03-31,101,103,100,104,1200\n"
    bars = parse_stooq_csv(raw)
    summary = summarize_bars(bars)
    assert len(bars) == 2
    assert summary["return_percent"] == 2.97
