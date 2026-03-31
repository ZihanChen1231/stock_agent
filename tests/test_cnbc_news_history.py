from app.tools.cnbc_news_client import parse_article_datetime


def test_parse_article_datetime_iso_zulu() -> None:
    parsed = parse_article_datetime("2026-03-31T12:00:00Z")
    assert parsed is not None
    assert parsed.year == 2026
