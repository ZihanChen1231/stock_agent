from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.schemas.analysis import ToolCallRecord
from app.tools.registry import ToolRegistry


@dataclass
class ReactResult:
    reasoning: list[str]
    tool_calls: list[ToolCallRecord]
    observations: dict[str, dict]


class ReactLoop:
    def __init__(self, tool_registry: ToolRegistry, max_iterations: int = 3) -> None:
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations

    async def run(self, ticker: str, question: str, company_name: Optional[str] = None) -> ReactResult:
        reasoning: list[str] = []
        tool_calls: list[ToolCallRecord] = []
        observations: dict[str, dict] = {}

        plan = self._build_plan(question)
        for iteration, tool_name in enumerate(plan[: self.max_iterations], start=1):
            arguments = {"ticker": ticker}
            if company_name:
                arguments["company_name"] = company_name

            reasoning.append(f"Iteration {iteration}: use `{tool_name}` to gather evidence relevant to the question.")
            tool = self.tool_registry.get(tool_name)
            output = await tool.invoke(arguments)
            observations[tool_name] = output
            tool_calls.append(ToolCallRecord(tool=tool_name, input=arguments, output=output))
            reasoning.append(f"Observed data from `{tool_name}` and updated the working thesis.")

        reasoning.append("Synthesized market data, news signals, and retrieved context into a final answer.")
        return ReactResult(reasoning=reasoning, tool_calls=tool_calls, observations=observations)

    def _build_plan(self, question: str) -> list[str]:
        lowered = question.lower()
        if any(keyword in lowered for keyword in ["news", "catalyst", "headline", "sentiment"]):
            return ["stock_news", "stock_price"]
        return ["stock_price", "stock_news"]
