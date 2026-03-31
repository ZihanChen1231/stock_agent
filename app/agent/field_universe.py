from __future__ import annotations


FIELD_UNIVERSE: dict[str, list[dict[str, str]]] = {
    "tech": [
        {"ticker": "AAPL", "company_name": "Apple"},
        {"ticker": "MSFT", "company_name": "Microsoft"},
        {"ticker": "NVDA", "company_name": "NVIDIA"},
        {"ticker": "GOOGL", "company_name": "Alphabet"},
        {"ticker": "META", "company_name": "Meta"},
        {"ticker": "AMZN", "company_name": "Amazon"},
    ],
    "finance": [
        {"ticker": "JPM", "company_name": "JPMorgan Chase"},
        {"ticker": "BAC", "company_name": "Bank of America"},
        {"ticker": "GS", "company_name": "Goldman Sachs"},
        {"ticker": "MS", "company_name": "Morgan Stanley"},
        {"ticker": "V", "company_name": "Visa"},
        {"ticker": "MA", "company_name": "Mastercard"},
    ],
    "energy": [
        {"ticker": "XOM", "company_name": "Exxon Mobil"},
        {"ticker": "CVX", "company_name": "Chevron"},
        {"ticker": "COP", "company_name": "ConocoPhillips"},
        {"ticker": "SLB", "company_name": "SLB"},
        {"ticker": "EOG", "company_name": "EOG Resources"},
        {"ticker": "PSX", "company_name": "Phillips 66"},
    ],
}


def get_field_universe(field: str) -> list[dict[str, str]]:
    normalized = field.strip().lower()
    return FIELD_UNIVERSE.get(normalized, [])
