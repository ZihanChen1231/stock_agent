from typing import Any
from typing import Optional

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol.")
    question: str = Field(..., min_length=5, description="User question for the agent.")
    company_name: Optional[str] = Field(default=None, description="Optional company name.")


class ToolCallRecord(BaseModel):
    tool: str
    input: dict[str, Any]
    output: dict[str, Any]


class AnalysisResponse(BaseModel):
    ticker: str
    question: str
    answer: str
    reasoning: list[str]
    retrieved_context: list[str]
    tool_calls: list[ToolCallRecord]
