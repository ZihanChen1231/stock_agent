from __future__ import annotations

from typing import Any

import httpx


class OllamaEmbedder:
    def __init__(self, model: str = "embeddinggemma", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.model,
                    "input": texts,
                    "truncate": True,
                },
            )
            if response.status_code == 404:
                return await self._embed_with_legacy_endpoint(client, texts)

            response.raise_for_status()
            data = response.json()
        return data["embeddings"]

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_texts([text])
        return vectors[0]

    async def _embed_with_legacy_endpoint(
        self,
        client: httpx.AsyncClient,
        texts: list[str],
    ) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for text in texts:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            vector = data.get("embedding")
            if not vector:
                raise ValueError("Legacy Ollama embeddings response did not include `embedding`.")
            embeddings.append(vector)
        return embeddings
