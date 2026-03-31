from __future__ import annotations

from typing import Any

from app.mcp.memory import InMemoryMemoryStore
from app.tools.registry import ToolRegistry


class MCPServer:
    def __init__(self, tool_registry: ToolRegistry, memory_store: InMemoryMemoryStore) -> None:
        self.tool_registry = tool_registry
        self.memory_store = memory_store

    async def handle(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = params or {}

        if method == "server.info":
            return {
                "name": "stock-agent-mcp",
                "version": "0.1.0",
                "capabilities": ["tools", "memory"],
            }

        if method == "tools.list":
            return {"tools": self.list_tools()}

        if method == "tools.call":
            tool_name = arguments["name"]
            tool_args = arguments.get("arguments", {})
            tool = self.tool_registry.get(tool_name)
            return {
                "tool": tool_name,
                "result": await tool.invoke(tool_args),
            }

        if method == "memory.put":
            entry = self.memory_store.put(
                ticker=arguments["ticker"],
                content=arguments["content"],
                metadata=arguments.get("metadata"),
            )
            return {"memory": self.memory_store._serialize(entry)}

        if method == "memory.search":
            return {
                "items": self.memory_store.search(
                    query=arguments["query"],
                    ticker=arguments.get("ticker"),
                    top_k=arguments.get("top_k", 3),
                )
            }

        if method == "memory.list":
            return {"items": self.memory_store.list(ticker=arguments.get("ticker"))}

        raise ValueError("Unsupported MCP method: {method}".format(method=method))

    def list_tools(self) -> list[dict[str, Any]]:
        return [tool.mcp_spec() for tool in self.tool_registry.all()]
