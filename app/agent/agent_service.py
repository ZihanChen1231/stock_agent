from __future__ import annotations

from app.agent.react_loop import ReactLoop
from app.core.config import Settings
from app.rag.pipeline import RagPipeline
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.tools.registry import ToolRegistry


class AgentService:
    def __init__(self, settings: Settings, rag_pipeline: RagPipeline, tool_registry: ToolRegistry) -> None:
        self.settings = settings
        self.rag_pipeline = rag_pipeline
        self.react_loop = ReactLoop(tool_registry=tool_registry, max_iterations=settings.max_iterations)

    async def analyze(self, request: AnalysisRequest) -> AnalysisResponse:
        retrieval_query = f"{request.ticker} {request.company_name or ''} {request.question}".strip()
        retrieved = self.rag_pipeline.retrieve(retrieval_query, top_k=self.settings.rag_top_k)
        trimmed_context = self._trim_context([item.content for item in retrieved])
        react_result = await self.react_loop.run(
            ticker=request.ticker,
            question=request.question,
            company_name=request.company_name,
        )
        answer = self._compose_answer(request, trimmed_context, react_result.observations)
        return AnalysisResponse(
            ticker=request.ticker.upper(),
            question=request.question,
            answer=answer,
            reasoning=react_result.reasoning,
            retrieved_context=trimmed_context,
            tool_calls=react_result.tool_calls,
        )

    def _trim_context(self, chunks: list[str]) -> list[str]:
        budget = self.settings.context_char_budget
        selected: list[str] = []
        used = 0
        for chunk in chunks:
            if used >= budget:
                break
            remaining = budget - used
            clipped = chunk[:remaining]
            if clipped:
                selected.append(clipped)
                used += len(clipped)
        return selected

    def _compose_answer(self, request: AnalysisRequest, context: list[str], observations: dict[str, dict]) -> str:
        price_data = observations.get("stock_price", {})
        news_data = observations.get("stock_news", {})

        current_price = price_data.get("current_price", "n/a")
        move_pct = price_data.get("day_change_percent", "n/a")
        headlines = [article.get("title") for article in news_data.get("articles", []) if article.get("title")]
        news_summary = "; ".join(headlines[:2]) if headlines else "No recent headlines were available."
        context_summary = context[0] if context else "No local reference context matched strongly enough to include."

        return (
            f"For {request.ticker.upper()}, the agent sees a current price near {current_price} "
            f"with a daily move of {move_pct}%. "
            f"Question focus: {request.question} "
            f"Recent signal summary: {news_summary} "
            f"Relevant local context: {context_summary}"
        )
