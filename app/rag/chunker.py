from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.rag.parser import ParsedDocument


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


class TextChunker:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 120) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: ParsedDocument) -> list[Chunk]:
        chunks = split_text(document.text, chunk_size=self.chunk_size, overlap=self.chunk_overlap)
        output: list[Chunk] = []
        for index, text in enumerate(chunks):
            metadata = dict(document.metadata)
            metadata.update({"chunk_index": index, "source_id": document.source_id})
            output.append(
                Chunk(
                    chunk_id=f"{document.source_id}-{index}",
                    text=text,
                    metadata=metadata,
                )
            )
        return output


def split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    normalized = " ".join(text.split())
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        boundary = normalized.rfind(". ", start, end)
        if boundary > start + int(chunk_size * 0.6):
            end = boundary + 1
        chunks.append(normalized[start:end].strip())
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks
