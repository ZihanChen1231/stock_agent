from __future__ import annotations

from typing import Any

from app.mcp.server import MCPServer


class LocalMCPClient:
    def __init__(self, server: MCPServer) -> None:
        self.server = server

    async def server_info(self) -> dict[str, Any]:
        return await self.server.handle("server.info")

    async def list_tools(self) -> dict[str, Any]:
        return await self.server.handle("tools.list")

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        response = await self.server.handle("tools.call", {"name": name, "arguments": arguments})
        return response["result"]

    async def put_memory(self, ticker: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        response = await self.server.handle(
            "memory.put",
            {"ticker": ticker, "content": content, "metadata": metadata or {}},
        )
        return response["memory"]

    async def search_memory(self, query: str, ticker: str | None = None, top_k: int = 3) -> list[dict[str, Any]]:
        response = await self.server.handle(
            "memory.search",
            {"query": query, "ticker": ticker, "top_k": top_k},
        )
        return response["items"]

    async def list_memory(self, ticker: str | None = None) -> list[dict[str, Any]]:
        response = await self.server.handle("memory.list", {"ticker": ticker})
        return response["items"]
