from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Optional

import httpx


@dataclass
class RawDocument:
    source_id: str
    content: str
    metadata: dict[str, Any]


class DocumentFetcher:
    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    async def fetch(self, source: dict[str, Any]) -> RawDocument:
        source_type = source.get("type", "file")
        if source_type == "url":
            return await self._fetch_url(source)
        return self._fetch_file(source)

    async def fetch_many(self, sources: list[dict[str, Any]]) -> list[RawDocument]:
        documents: list[RawDocument] = []
        for source in sources:
            documents.append(await self.fetch(source))
        return documents

    async def _fetch_url(self, source: dict[str, Any]) -> RawDocument:
        url = source["location"]
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        metadata = dict(source.get("metadata", {}))
        metadata.update({"origin": "url", "url": url, "content_type": response.headers.get("content-type")})
        return RawDocument(
            source_id=source.get("id", url),
            content=response.text,
            metadata=metadata,
        )

    def _fetch_file(self, source: dict[str, Any]) -> RawDocument:
        location = Path(source["location"]).expanduser().resolve()
        content = location.read_text(encoding=source.get("encoding", "utf-8"))
        metadata = dict(source.get("metadata", {}))
        metadata.update({"origin": "file", "path": str(location)})
        return RawDocument(
            source_id=source.get("id", location.name),
            content=content,
            metadata=metadata,
        )


def load_sources_file(path: str) -> list[dict[str, Any]]:
    source_path = Path(path).expanduser().resolve()
    if source_path.suffix.lower() == ".json":
        import json

        payload = json.loads(source_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return payload.get("sources", [])
        return payload

    lines = [line.strip() for line in source_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [{"type": infer_source_type(line), "location": line} for line in lines]


def infer_source_type(location: str) -> str:
    if location.startswith("http://") or location.startswith("https://"):
        return "url"
    return "file"
