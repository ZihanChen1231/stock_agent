from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from typing import Optional

from app.rag.embedder import OllamaEmbedder
from app.rag.store import ChromaStore


@dataclass
class RetrievedChunk:
    chunk_id: str
    source: str
    content: str
    metadata: dict[str, Any]
    distance: Optional[float]


class ChromaRetriever:
    def __init__(self, store: ChromaStore, embedder: OllamaEmbedder) -> None:
        self.store = store
        self.embedder = embedder

    async def retrieve(self, query: str, top_k: int = 3, field: Optional[str] = None) -> list[RetrievedChunk]:
        query_embedding = await self.embedder.embed_text(query)
        results = self.store.query(query_embedding=query_embedding, n_results=top_k, where=build_where(field))
        output: list[RetrievedChunk] = []
        for item in results:
            metadata = item.get("metadata", {})
            output.append(
                RetrievedChunk(
                    chunk_id=item["id"],
                    source=str(metadata.get("path") or metadata.get("url") or metadata.get("source_id") or "unknown"),
                    content=item.get("document", ""),
                    metadata=metadata,
                    distance=item.get("distance"),
                )
            )
        return output

    def verify(self, limit: int = 10, field: Optional[str] = None) -> dict[str, Any]:
        where = build_where(field)
        preview = self.store.peek(limit=limit, where=where)
        return {
            "collection": self.store.collection_name,
            "count": self.store.count(where=where),
            "items": preview,
        }


def build_where(field: Optional[str]) -> Optional[dict[str, Any]]:
    if not field:
        return None
    return {"field": field}
