from functools import lru_cache

from app.agent.agent_service import AgentService
from app.core.config import get_settings
from app.rag.pipeline import RagPipeline
from app.tools.registry import ToolRegistry


@lru_cache(maxsize=1)
def get_agent_service() -> AgentService:
    settings = get_settings()
    rag = RagPipeline.from_knowledge_dir(
        "data/knowledge",
        chunk_size=settings.rag_chunk_size,
        overlap=settings.rag_chunk_overlap,
    )
    registry = ToolRegistry.from_settings(settings)
    return AgentService(settings=settings, rag_pipeline=rag, tool_registry=registry)
