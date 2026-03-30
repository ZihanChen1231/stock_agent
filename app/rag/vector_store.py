from __future__ import annotations

import math
import re
from collections import Counter


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._documents: list[dict[str, str]] = []
        self._vectors: list[Counter[str]] = []

    def add(self, document_id: str, content: str, metadata: dict[str, str]) -> None:
        self._documents.append(
            {
                "document_id": document_id,
                "content": content,
                "source": metadata.get("source", document_id),
            }
        )
        self._vectors.append(Counter(tokenize(content)))

    def search(self, query: str, top_k: int = 3) -> list[dict[str, str]]:
        query_vector = Counter(tokenize(query))
        scored: list[tuple[float, dict[str, str]]] = []
        for document, vector in zip(self._documents, self._vectors):
            score = cosine_similarity(query_vector, vector)
            if score > 0:
                scored.append((score, document))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [document for _, document in scored[:top_k]]


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    dot = sum(left[token] * right[token] for token in left.keys() & right.keys())
    if dot == 0:
        return 0.0

    left_mag = math.sqrt(sum(value * value for value in left.values()))
    right_mag = math.sqrt(sum(value * value for value in right.values()))
    if left_mag == 0 or right_mag == 0:
        return 0.0
    return dot / (left_mag * right_mag)
