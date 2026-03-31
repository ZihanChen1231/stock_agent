from typing import Optional

from fastapi import Depends
from fastapi import FastAPI

from app.mcp.dependencies import get_mcp_server
from app.mcp.models import MCPRequest
from app.mcp.models import MCPResponse
from app.mcp.models import MCPToolCallRequest
from app.mcp.models import MemoryPutRequest
from app.mcp.models import MemorySearchRequest
from app.mcp.server import MCPServer


app = FastAPI(
    title="Stock Agent MCP Server",
    version="0.1.0",
    description="Standalone MCP-style service for stock tools and memory.",
)


@app.get("/health", response_model=dict[str, str])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/info", response_model=MCPResponse)
async def mcp_info(server: MCPServer = Depends(get_mcp_server)) -> MCPResponse:
    return MCPResponse(result=await server.handle("server.info"))


@app.get("/tools", response_model=MCPResponse)
async def mcp_tools(server: MCPServer = Depends(get_mcp_server)) -> MCPResponse:
    return MCPResponse(result=await server.handle("tools.list"))


@app.post("/tools/call", response_model=MCPResponse)
async def mcp_call_tool(
    request: MCPToolCallRequest,
    server: MCPServer = Depends(get_mcp_server),
) -> MCPResponse:
    return MCPResponse(result=await server.handle("tools.call", {"name": request.name, "arguments": request.arguments}))


@app.get("/quote/{ticker}", response_model=MCPResponse)
async def get_quote(ticker: str, server: MCPServer = Depends(get_mcp_server)) -> MCPResponse:
    return MCPResponse(result=await server.handle("tools.call", {"name": "get_stock_price", "arguments": {"ticker": ticker}}))


@app.get("/news/{ticker}", response_model=MCPResponse)
async def get_news(
    ticker: str,
    company_name: Optional[str] = None,
    max_items: int = 5,
    server: MCPServer = Depends(get_mcp_server),
) -> MCPResponse:
    return MCPResponse(
        result=await server.handle(
            "tools.call",
            {
                "name": "get_stock_news",
                "arguments": {
                    "ticker": ticker,
                    "company_name": company_name,
                    "max_items": max_items,
                },
            },
        )
    )


@app.post("/memory", response_model=MCPResponse)
async def mcp_put_memory(
    request: MemoryPutRequest,
    server: MCPServer = Depends(get_mcp_server),
) -> MCPResponse:
    return MCPResponse(
        result=await server.handle(
            "memory.put",
            {"ticker": request.ticker, "content": request.content, "metadata": request.metadata},
        )
    )


@app.post("/memory/search", response_model=MCPResponse)
async def mcp_search_memory(
    request: MemorySearchRequest,
    server: MCPServer = Depends(get_mcp_server),
) -> MCPResponse:
    return MCPResponse(
        result=await server.handle(
            "memory.search",
            {"query": request.query, "ticker": request.ticker, "top_k": request.top_k},
        )
    )


@app.post("/mcp", response_model=MCPResponse)
async def mcp_rpc(
    request: MCPRequest,
    server: MCPServer = Depends(get_mcp_server),
) -> MCPResponse:
    return MCPResponse(result=await server.handle(request.method, request.params))
