from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from html import unescape
from typing import Any
from typing import Optional

import httpx


QUOTE_URL_TEMPLATE = "https://www.cnbc.com/quotes/{ticker}"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


class CNBCNewsClient:
    async def fetch_stock_news(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        max_items: int = 5,
    ) -> list[dict[str, Any]]:
        html = await self._fetch_quote_page(ticker)
        items = parse_cnbc_quote_news(html=html, ticker=ticker, company_name=company_name, max_items=max_items)
        if items:
            return items
        raise ValueError("Unable to extract CNBC news items from quote page")

    async def fetch_stock_news_history(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        past_days: int = 7,
        max_items: int = 10,
    ) -> dict[str, Any]:
        articles = await self.fetch_stock_news(ticker=ticker, company_name=company_name, max_items=max_items * 2)
        cutoff = datetime.now(timezone.utc) - timedelta(days=past_days)
        filtered = []
        for article in articles:
            published = parse_article_datetime(article.get("published_at"))
            if published is None or published >= cutoff:
                filtered.append(article)
            if len(filtered) >= max_items:
                break

        if not filtered:
            filtered = articles[:max_items]

        return {
            "ticker": ticker.upper(),
            "past_days": past_days,
            "articles": filtered,
            "article_count": len(filtered),
            "source": "cnbc_direct",
        }

    async def _fetch_quote_page(self, ticker: str) -> str:
        url = QUOTE_URL_TEMPLATE.format(ticker=ticker.upper())
        headers = {"User-Agent": USER_AGENT}
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text


def parse_cnbc_quote_news(
    html: str,
    ticker: str,
    company_name: Optional[str],
    max_items: int,
) -> list[dict[str, Any]]:
    for extractor in (extract_from_json_blocks, extract_from_ld_json, extract_from_anchor_markup):
        items = extractor(html)
        normalized = normalize_cnbc_items(items=items, ticker=ticker, company_name=company_name, max_items=max_items)
        if normalized:
            return normalized
    return []


def extract_from_json_blocks(html: str) -> list[dict[str, Any]]:
    patterns = [
        r'"latestNews"\s*:\s*(\[[\s\S]*?\])',
        r'"quoteNews"\s*:\s*(\[[\s\S]*?\])',
        r'"news"\s*:\s*(\[[\s\S]*?\])',
    ]
    for pattern in patterns:
        match = re.search(pattern, html)
        if not match:
            continue
        parsed = try_load_json_array(match.group(1))
        if parsed:
            return parsed
    return []


def extract_from_ld_json(html: str) -> list[dict[str, Any]]:
    matches = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>\s*([\s\S]*?)\s*</script>',
        html,
        flags=re.IGNORECASE,
    )
    items: list[dict[str, Any]] = []
    for raw_block in matches:
        try:
            data = json.loads(unescape(raw_block))
        except json.JSONDecodeError:
            continue

        candidates = data if isinstance(data, list) else [data]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            graph_items = candidate.get("@graph", [])
            if isinstance(graph_items, list):
                for graph_item in graph_items:
                    if is_news_article(graph_item):
                        items.append(graph_item)
            elif is_news_article(candidate):
                items.append(candidate)
    return items


def extract_from_anchor_markup(html: str) -> list[dict[str, Any]]:
    anchor_matches = re.findall(
        r'<a[^>]+href="(https://www\.cnbc\.com/[^"]+)"[^>]*>([\s\S]*?)</a>',
        html,
        flags=re.IGNORECASE,
    )
    items: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for url, inner_html in anchor_matches:
        if "/video/" in url or url in seen_urls:
            continue
        title = clean_html_text(inner_html)
        if not title or len(title) < 20:
            continue
        seen_urls.add(url)
        items.append({"title": title, "url": url, "source": "CNBC"})
    return items


def normalize_cnbc_items(
    items: list[dict[str, Any]],
    ticker: str,
    company_name: Optional[str],
    max_items: int,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    ticker_lower = ticker.lower()
    company_lower = (company_name or "").strip().lower()

    for item in items:
        title = pick_text(item, ["title", "headline", "name"])
        summary = pick_text(item, ["description", "summary", "deck"])
        url = pick_text(item, ["url", "mainEntityOfPage"])
        published_at = pick_text(item, ["datePublished", "publishedAt", "dateCreated"])
        source = pick_source(item)

        haystack = " ".join(part for part in [title, summary, url] if part).lower()
        if company_lower and company_lower not in haystack and ticker_lower not in haystack:
            continue

        normalized.append(
            {
                "title": title or "Untitled CNBC item",
                "summary": summary,
                "source": source or "CNBC",
                "url": url or None,
                "published_at": published_at or None,
            }
        )
        if len(normalized) >= max_items:
            break

    if normalized:
        return normalized

    fallback: list[dict[str, Any]] = []
    for item in items[:max_items]:
        fallback.append(
            {
                "title": pick_text(item, ["title", "headline", "name"]) or "Untitled CNBC item",
                "summary": pick_text(item, ["description", "summary", "deck"]),
                "source": pick_source(item) or "CNBC",
                "url": pick_text(item, ["url", "mainEntityOfPage"]) or None,
                "published_at": pick_text(item, ["datePublished", "publishedAt", "dateCreated"]) or None,
            }
        )
    return fallback


def try_load_json_array(raw: str) -> list[dict[str, Any]]:
    for candidate in (raw, raw.replace('\\"', '"')):
        try:
            data = json.loads(unescape(candidate))
        except json.JSONDecodeError:
            continue
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    return []


def is_news_article(item: Any) -> bool:
    if not isinstance(item, dict):
        return False
    item_type = item.get("@type")
    if item_type == "NewsArticle":
        return True
    if isinstance(item_type, list) and "NewsArticle" in item_type:
        return True
    return False


def pick_text(item: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = item.get(key)
        if isinstance(value, dict):
            nested_url = value.get("@id") or value.get("url")
            if nested_url:
                return str(nested_url)
        if value not in (None, ""):
            return clean_html_text(str(value))
    return ""


def pick_source(item: dict[str, Any]) -> str:
    value = item.get("source") or item.get("publisher")
    if isinstance(value, dict):
        name = value.get("name")
        if name:
            return str(name)
    if value not in (None, ""):
        return str(value)
    return ""


def clean_html_text(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text)
    squashed = re.sub(r"\s+", " ", unescape(without_tags))
    return squashed.strip()


def parse_article_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = value.strip()
    try:
        if text.endswith("Z"):
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None
