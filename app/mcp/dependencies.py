from functools import lru_cache

from app.core.config import get_settings
from app.mcp.memory import InMemoryMemoryStore
from app.mcp.server import MCPServer
from app.tools.registry import ToolRegistry


@lru_cache(maxsize=1)
def get_mcp_server() -> MCPServer:
    settings = get_settings()
    registry = ToolRegistry.from_settings(settings)
    memory_store = InMemoryMemoryStore()
    return MCPServer(tool_registry=registry, memory_store=memory_store)
