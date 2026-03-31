from app.tools.cnbc_news_client import parse_cnbc_quote_news


def test_parse_cnbc_quote_news_from_json_block() -> None:
    html = """
    <html>
      <script>
        window.__DATA__ = {"latestNews":[
          {"title":"Apple shares rise after new product event","description":"AAPL investors react.","url":"https://www.cnbc.com/2026/03/30/apple-rise.html","datePublished":"2026-03-30T12:00:00Z","source":"CNBC"},
          {"title":"Oil falls on demand concerns","description":"Energy update.","url":"https://www.cnbc.com/2026/03/30/oil-falls.html","datePublished":"2026-03-30T11:00:00Z","source":"CNBC"}
        ]};
      </script>
    </html>
    """

    result = parse_cnbc_quote_news(html=html, ticker="AAPL", company_name="Apple", max_items=5)

    assert len(result) == 1
    assert result[0]["title"] == "Apple shares rise after new product event"
    assert result[0]["source"] == "CNBC"


def test_parse_cnbc_quote_news_from_ld_json() -> None:
    html = """
    <html>
      <script type="application/ld+json">
        {
          "@graph": [
            {
              "@type": "NewsArticle",
              "headline": "Apple expands its AI push",
              "description": "The iPhone maker outlined fresh plans.",
              "url": "https://www.cnbc.com/2026/03/30/apple-ai-push.html",
              "datePublished": "2026-03-30T09:30:00Z",
              "publisher": {"name": "CNBC"}
            }
          ]
        }
      </script>
    </html>
    """

    result = parse_cnbc_quote_news(html=html, ticker="AAPL", company_name="Apple", max_items=5)

    assert len(result) == 1
    assert result[0]["title"] == "Apple expands its AI push"
    assert result[0]["url"] == "https://www.cnbc.com/2026/03/30/apple-ai-push.html"
