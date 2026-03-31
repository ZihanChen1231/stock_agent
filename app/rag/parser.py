from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from typing import Any

from app.rag.fetcher import RawDocument


@dataclass
class ParsedDocument:
    source_id: str
    title: str
    text: str
    metadata: dict[str, Any]


class DocumentParser:
    def parse(self, document: RawDocument) -> ParsedDocument:
        content_type = str(document.metadata.get("content_type", "")).lower()
        title = str(document.metadata.get("title") or document.source_id)

        if "html" in content_type or looks_like_html(document.content):
            parsed_title, parsed_text = parse_html(document.content)
            if parsed_title:
                title = parsed_title
        else:
            parsed_text = clean_text(document.content)

        metadata = dict(document.metadata)
        metadata["title"] = title
        return ParsedDocument(
            source_id=document.source_id,
            title=title,
            text=parsed_text,
            metadata=metadata,
        )


def parse_html(html: str) -> tuple[str, str]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = clean_text(title_match.group(1)) if title_match else ""

    stripped = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    stripped = re.sub(r"<style[\s\S]*?</style>", " ", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"<[^>]+>", " ", stripped)
    return title, clean_text(stripped)


def clean_text(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def looks_like_html(content: str) -> bool:
    lowered = content[:500].lower()
    return "<html" in lowered or "<body" in lowered or "<div" in lowered
