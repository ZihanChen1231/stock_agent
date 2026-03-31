from functools import lru_cache

from app.agent.agent_service import AgentService
from app.core.config import get_settings
from app.mcp.client import LocalMCPClient
from app.mcp.dependencies import get_mcp_server
from app.rag.embedder import OllamaEmbedder
from app.rag.pipeline import RagPipeline
from app.rag.retriever import ChromaRetriever
from app.rag.store import ChromaStore


@lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
    settings = get_settings()
    rag = RagPipeline.from_knowledge_dir(
        "data/knowledge",
        chunk_size=settings.rag_chunk_size,
        overlap=settings.rag_chunk_overlap,
    )
    mcp_client = LocalMCPClient(server=get_mcp_server())
    chroma_retriever = get_chroma_retriever()
    return AgentService(settings=settings, rag_pipeline=rag, mcp_client=mcp_client, chroma_retriever=chroma_retriever)


@lru_cache(maxsize=1)
def get_chroma_retriever() -> ChromaRetriever:
    settings = get_settings()
    store = ChromaStore(
        collection_name=settings.chroma_collection,
        host=settings.chroma_host,
        port=settings.chroma_port,
    )
    embedder = OllamaEmbedder(model=settings.embedding_model, base_url=settings.ollama_url)
    return ChromaRetriever(store=store, embedder=embedder)
