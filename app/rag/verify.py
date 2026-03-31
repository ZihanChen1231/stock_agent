from __future__ import annotations

import argparse
import json

from app.core.config import get_settings
from app.rag.embedder import OllamaEmbedder
from app.rag.retriever import ChromaRetriever
from app.rag.store import ChromaStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify documents ingested into Chroma.")
    parser.add_argument("--collection", help="Override collection name.")
    parser.add_argument("--field", help="Optional field filter, such as tech or energy.")
    parser.add_argument("--limit", type=int, default=10, help="Number of preview rows to return.")
    return parser


def main() -> None:
    settings = get_settings()
    parser = build_parser()
    args = parser.parse_args()

    store = ChromaStore(
        collection_name=args.collection or settings.chroma_collection,
        host=settings.chroma_host,
        port=settings.chroma_port,
    )
    retriever = ChromaRetriever(
        store=store,
        embedder=OllamaEmbedder(model=settings.embedding_model, base_url=settings.ollama_url),
    )
    print(json.dumps(retriever.verify(limit=args.limit, field=args.field), indent=2))


if __name__ == "__main__":
    main()
