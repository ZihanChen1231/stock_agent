from typing import Any
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class RagVerifyResponse(BaseModel):
    collection: str
    count: int
    items: list[dict[str, Any]]


class RagRetrieveRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_k: int = Field(default=3, ge=1, le=10)
    field: Optional[str] = None


class RagRetrieveResponse(BaseModel):
    query: str
    results: list[dict[str, Any]]
