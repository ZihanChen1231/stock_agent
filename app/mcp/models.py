from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class MCPRequest(BaseModel):
    method: str = Field(..., description="MCP method name.")
    params: dict[str, Any] = Field(default_factory=dict, description="MCP method arguments.")


class MCPResponse(BaseModel):
    ok: bool = True
    result: dict[str, Any]


class MCPToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class MemoryPutRequest(BaseModel):
    ticker: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    top_k: int = 3
