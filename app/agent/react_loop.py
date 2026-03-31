from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.mcp.client import LocalMCPClient
from app.schemas.analysis import ToolCallRecord


@dataclass
class ReactResult:
    reasoning: list[str]
    tool_calls: list[ToolCallRecord]
    observations: dict[str, dict]


class ReactLoop:
    def __init__(self, mcp_client: LocalMCPClient, max_iterations: int = 3) -> None:
        self.mcp_client = mcp_client
        self.max_iterations = max_iterations

    async def run(self, ticker: str, question: str, company_name: Optional[str] = None) -> ReactResult:
        reasoning: list[str] = []
        tool_calls: list[ToolCallRecord] = []
        observations: dict[str, dict] = {}

        memories = await self.mcp_client.search_memory(query=question, ticker=ticker, top_k=2)
        if memories:
            observations["memory_search"] = {"items": memories}
            reasoning.append("Reviewed relevant prior memory before calling external tools.")

        plan = self._build_plan(question)
        for iteration, tool_name in enumerate(plan[: self.max_iterations], start=1):
            arguments = {"ticker": ticker}
            if company_name:
                arguments["company_name"] = company_name

            reasoning.append(f"Iteration {iteration}: use `{tool_name}` to gather evidence relevant to the question.")
            output = await self.mcp_client.call_tool(tool_name, arguments)
            observations[tool_name] = output
            tool_calls.append(ToolCallRecord(tool=tool_name, input=arguments, output=output))
            reasoning.append(f"Observed data from `{tool_name}` and updated the working thesis.")

        reasoning.append("Synthesized market data, news signals, and retrieved context into a final answer.")
        return ReactResult(reasoning=reasoning, tool_calls=tool_calls, observations=observations)

    def _build_plan(self, question: str) -> list[str]:
        lowered = question.lower()
        if any(keyword in lowered for keyword in ["news", "catalyst", "headline", "sentiment"]):
            return ["get_stock_news", "get_stock_price"]
        return ["get_stock_price", "get_stock_news"]
