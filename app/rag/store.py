from __future__ import annotations

from typing import Any
from typing import Optional

from chromadb import HttpClient

from app.rag.chunker import Chunk


class ChromaStore:
    def __init__(
        self,
        collection_name: str = "stock-knowledge",
        host: str = "localhost",
        port: int = 8000,
    ) -> None:
        self.collection_name = collection_name
        self.client = HttpClient(host=host, port=port)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def upsert_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        if not chunks:
            return 0

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [sanitize_metadata(chunk.metadata) for chunk in chunks]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        return len(chunks)

    def count(self, where: Optional[dict[str, Any]] = None) -> int:
        if where:
            result = self.collection.get(where=where, include=[])
            return len(result.get("ids", []))
        return self.collection.count()

    def peek(self, limit: int = 10, where: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
        result = self.collection.get(limit=limit, where=where, include=["documents", "metadatas"])
        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        items: list[dict[str, Any]] = []
        for index, item_id in enumerate(ids):
            items.append(
                {
                    "id": item_id,
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "document_preview": (documents[index] if index < len(documents) else "")[:300],
                }
            )
        return items

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 3,
        where: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        items: list[dict[str, Any]] = []
        for index, item_id in enumerate(ids):
            items.append(
                {
                    "id": item_id,
                    "document": documents[index] if index < len(documents) else "",
                    "metadata": metadatas[index] if index < len(metadatas) else {},
                    "distance": distances[index] if index < len(distances) else None,
                }
            )
        return items


def sanitize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean
