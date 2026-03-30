from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.rag.vector_store import InMemoryVectorStore


@dataclass
class RetrievedChunk:
    source: str
    content: str


class RagPipeline:
    def __init__(self, store: InMemoryVectorStore) -> None:
        self.store = store

    @classmethod
    def from_knowledge_dir(cls, knowledge_dir: str, chunk_size: int = 500, overlap: int = 80) -> "RagPipeline":
        base_path = Path(knowledge_dir)
        store = InMemoryVectorStore()
        if base_path.exists():
            for path in sorted(base_path.glob("**/*")):
                if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                    continue
                content = path.read_text(encoding="utf-8")
                for index, chunk in enumerate(chunk_text(content, chunk_size=chunk_size, overlap=overlap)):
                    store.add(
                        document_id=f"{path.name}-{index}",
                        content=chunk,
                        metadata={"source": str(path)},
                    )
        return cls(store)

    def retrieve(self, query: str, top_k: int = 3) -> list[RetrievedChunk]:
        results = self.store.search(query=query, top_k=top_k)
        return [RetrievedChunk(source=item["source"], content=item["content"]) for item in results]


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(normalized[start:end])
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
