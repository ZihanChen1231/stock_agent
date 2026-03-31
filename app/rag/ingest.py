from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.rag.chunker import TextChunker
from app.rag.embedder import OllamaEmbedder
from app.rag.fetcher import DocumentFetcher
from app.rag.fetcher import infer_source_type
from app.rag.fetcher import load_sources_file
from app.rag.parser import DocumentParser
from app.rag.store import ChromaStore


async def run_ingestion(args: argparse.Namespace) -> dict[str, Any]:
    sources = resolve_sources(args)
    fetcher = DocumentFetcher()
    parser = DocumentParser()
    chunker = TextChunker(chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    embedder = OllamaEmbedder(model=args.embedding_model, base_url=args.ollama_url)
    store = ChromaStore(collection_name=args.collection, host=args.chroma_host, port=args.chroma_port)

    raw_documents = await fetcher.fetch_many(sources)
    parsed_documents = [parser.parse(document) for document in raw_documents]

    chunks = []
    for document in parsed_documents:
        chunks.extend(chunker.chunk_document(document))

    embeddings = await embedder.embed_texts([chunk.text for chunk in chunks])
    written = store.upsert_chunks(chunks, embeddings)

    summary = {
        "collection": args.collection,
        "sources": len(raw_documents),
        "chunks": written,
        "embedding_model": args.embedding_model,
        "chroma_url": f"http://{args.chroma_host}:{args.chroma_port}",
    }
    return summary


def resolve_sources(args: argparse.Namespace) -> list[dict[str, Any]]:
    if args.sources_file:
        return load_sources_file(args.sources_file)

    sources: list[dict[str, Any]] = []
    for value in args.source:
        metadata = {}
        if args.field:
            metadata["field"] = args.field
        sources.append(
            {
                "id": Path(value).stem if "://" not in value else value,
                "type": infer_source_type(value),
                "location": value,
                "metadata": metadata,
            }
        )
    return sources


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest stock knowledge into ChromaDB with Ollama embeddings.")
    parser.add_argument("--source", action="append", default=[], help="Source file path or URL. Repeatable.")
    parser.add_argument("--sources-file", help="Path to a JSON manifest or line-based sources file.")
    parser.add_argument("--field", help="Optional sector/field metadata such as tech or energy.")
    parser.add_argument("--collection", default="stock-knowledge", help="Chroma collection name.")
    parser.add_argument("--chunk-size", type=int, default=900, help="Chunk size in characters.")
    parser.add_argument("--chunk-overlap", type=int, default=120, help="Chunk overlap in characters.")
    parser.add_argument("--embedding-model", default="embeddinggemma", help="Ollama embedding model name.")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Base URL for Ollama.")
    parser.add_argument("--chroma-host", default="localhost", help="Chroma host.")
    parser.add_argument("--chroma-port", type=int, default=8000, help="Chroma port.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.source and not args.sources_file:
        parser.error("Provide at least one --source or a --sources-file.")

    summary = asyncio.run(run_ingestion(args))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
