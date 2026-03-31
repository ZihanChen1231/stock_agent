from app.agent.field_universe import get_field_universe


def test_get_field_universe_returns_known_candidates() -> None:
    candidates = get_field_universe("tech")
    assert candidates
    assert any(item["ticker"] == "AAPL" for item in candidates)
