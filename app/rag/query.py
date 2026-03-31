from __future__ import annotations

import argparse
import asyncio
import json

from app.core.config import get_settings
from app.rag.embedder import OllamaEmbedder
from app.rag.retriever import ChromaRetriever
from app.rag.store import ChromaStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query Chroma-backed stock knowledge.")
    parser.add_argument("--query", required=True, help="Natural-language retrieval query.")
    parser.add_argument("--collection", help="Override collection name.")
    parser.add_argument("--field", help="Optional field filter, such as tech or finance.")
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks.")
    return parser


async def run() -> None:
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
    results = await retriever.retrieve(query=args.query, top_k=args.top_k, field=args.field)
    print(
        json.dumps(
            {
                "query": args.query,
                "collection": store.collection_name,
                "results": [
                    {
                        "chunk_id": item.chunk_id,
                        "source": item.source,
                        "distance": item.distance,
                        "metadata": item.metadata,
                        "content": item.content,
                    }
                    for item in results
                ],
            },
            indent=2,
        )
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
