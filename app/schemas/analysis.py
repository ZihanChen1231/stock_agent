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


class FieldAnalysisRequest(BaseModel):
    field: str = Field(..., min_length=2, description="Sector or field such as tech, finance, or energy.")
    top_x: int = Field(default=3, ge=1, le=10, description="Number of ranked stocks to return.")
    past_days: int = Field(default=7, ge=1, le=90, description="Recent time window in days for analysis framing.")
    question: str = Field(
        default="Which stocks look strongest in this field and why?",
        description="Optional custom question for the field analysis.",
    )


class RankedStock(BaseModel):
    rank: int
    ticker: str
    company_name: str
    rationale: str
    supporting_signals: list[str]


class FieldAnalysisResponse(BaseModel):
    field: str
    top_x: int
    past_days: int
    answer: str
    ranked_stocks: list[RankedStock]
    retrieved_context: list[str]
    tool_calls: list[ToolCallRecord]
