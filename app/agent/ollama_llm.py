from __future__ import annotations

import json
from typing import Any

import httpx


class OllamaLLM:
    def __init__(self, model: str = "mistral", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            data = response.json()

        raw_response = data.get("response", "").strip()
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return extract_json_object(raw_response)


def extract_json_object(raw: str) -> dict[str, Any]:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("Ollama response did not contain valid JSON.")
    return json.loads(raw[start : end + 1])
