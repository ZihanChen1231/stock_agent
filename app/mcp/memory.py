from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.rag.vector_store import cosine_similarity, tokenize


@dataclass
class MemoryEntry:
    memory_id: str
    ticker: str
    content: str
    metadata: dict
    created_at: str


class InMemoryMemoryStore:
    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    def put(self, ticker: str, content: str, metadata: Optional[dict] = None) -> MemoryEntry:
        next_id = f"mem-{len(self._entries) + 1}"
        entry = MemoryEntry(
            memory_id=next_id,
            ticker=ticker.upper(),
            content=content,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._entries.append(entry)
        return entry

    def search(self, query: str, ticker: Optional[str] = None, top_k: int = 3) -> list[dict]:
        query_tokens = tokenize(query)
        scored: list[tuple[float, MemoryEntry]] = []

        for entry in self._entries:
            if ticker and entry.ticker != ticker.upper():
                continue
            score = cosine_similarity(
                left=to_counter(query_tokens),
                right=to_counter(tokenize(entry.content)),
            )
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._serialize(entry) for _, entry in scored[:top_k]]

    def list(self, ticker: Optional[str] = None) -> list[dict]:
        entries = self._entries
        if ticker:
            entries = [entry for entry in entries if entry.ticker == ticker.upper()]
        return [self._serialize(entry) for entry in entries]

    def _serialize(self, entry: MemoryEntry) -> dict:
        return {
            "memory_id": entry.memory_id,
            "ticker": entry.ticker,
            "content": entry.content,
            "metadata": entry.metadata,
            "created_at": entry.created_at,
        }


def to_counter(tokens: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    return counts
