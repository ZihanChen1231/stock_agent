from __future__ import annotations

import json

from app.agent.field_universe import get_field_universe
from app.agent.ollama_llm import OllamaLLM
from app.agent.react_loop import ReactLoop
from app.core.config import Settings
from app.mcp.client import LocalMCPClient
from app.rag.retriever import ChromaRetriever
from app.schemas.analysis import AnalysisRequest, AnalysisResponse, FieldAnalysisRequest, FieldAnalysisResponse, RankedStock, ToolCallRecord


class AgentService:
    def __init__(self, settings: Settings, rag_pipeline, mcp_client: LocalMCPClient, chroma_retriever: ChromaRetriever) -> None:
        self.settings = settings
        self.rag_pipeline = rag_pipeline
        self.mcp_client = mcp_client
        self.chroma_retriever = chroma_retriever
        self.llm = OllamaLLM(model=settings.llm_model, base_url=settings.ollama_url)
        self.react_loop = ReactLoop(mcp_client=mcp_client, max_iterations=settings.max_iterations)

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
        await self.mcp_client.put_memory(
            ticker=request.ticker,
            content=answer,
            metadata={"question": request.question},
        )
        return AnalysisResponse(
            ticker=request.ticker.upper(),
            question=request.question,
            answer=answer,
            reasoning=react_result.reasoning,
            retrieved_context=trimmed_context,
            tool_calls=react_result.tool_calls,
        )

    async def analyze_field(self, request: FieldAnalysisRequest) -> FieldAnalysisResponse:
        candidates = get_field_universe(request.field)
        if not candidates:
            raise ValueError(f"Unsupported field `{request.field}`. Add it to the field universe first.")

        tool_calls: list[ToolCallRecord] = []
        candidate_summaries: list[dict[str, object]] = []

        for candidate in candidates:
            ticker = candidate["ticker"]
            company_name = candidate["company_name"]

            price_input = {"ticker": ticker}
            price_output = await self.mcp_client.call_tool("get_stock_price", price_input)
            tool_calls.append(ToolCallRecord(tool="get_stock_price", input=price_input, output=price_output))

            price_history_input = {"ticker": ticker, "past_days": request.past_days}
            price_history_output = await self.mcp_client.call_tool("get_stock_price_history", price_history_input)
            tool_calls.append(
                ToolCallRecord(tool="get_stock_price_history", input=price_history_input, output=price_history_output)
            )

            news_input = {"ticker": ticker, "company_name": company_name, "max_items": min(5, request.past_days)}
            news_output = await self.mcp_client.call_tool("get_stock_news", news_input)
            tool_calls.append(ToolCallRecord(tool="get_stock_news", input=news_input, output=news_output))

            news_history_input = {
                "ticker": ticker,
                "company_name": company_name,
                "past_days": request.past_days,
                "max_items": min(10, request.past_days),
            }
            news_history_output = await self.mcp_client.call_tool("get_stock_news_history", news_history_input)
            tool_calls.append(
                ToolCallRecord(tool="get_stock_news_history", input=news_history_input, output=news_history_output)
            )

            candidate_summaries.append(
                {
                    "ticker": ticker,
                    "company_name": company_name,
                    "price": {
                        "current_price": price_output.get("current_price"),
                        "day_change_percent": price_output.get("day_change_percent"),
                        "source": price_output.get("source"),
                    },
                    "price_history": price_history_output.get("summary", {}),
                    "news_headlines": [
                        article.get("title")
                        for article in news_output.get("articles", [])
                        if article.get("title")
                    ][:5],
                    "news_history": [
                        {
                            "title": article.get("title"),
                            "published_at": article.get("published_at"),
                        }
                        for article in news_history_output.get("articles", [])
                        if article.get("title")
                    ][:10],
                }
            )

        retrieval_query = (
            f"best {request.top_x} stocks in {request.field} over the past {request.past_days} days "
            f"{request.question}"
        )
        retrieved = await self.chroma_retriever.retrieve(
            query=retrieval_query,
            top_k=self.settings.rag_top_k,
            field=request.field,
        )
        retrieved_context = self._trim_context([item.content for item in retrieved])

        llm_payload = {
            "field": request.field,
            "top_x": request.top_x,
            "past_days": request.past_days,
            "question": request.question,
            "candidates": candidate_summaries,
            "retrieved_context": retrieved_context,
        }
        prompt = self._build_field_analysis_prompt(llm_payload)
        llm_response = await self.llm.generate_json(prompt)

        ranked_items = llm_response.get("ranked_stocks", [])[: request.top_x]
        ranked_stocks = [
            RankedStock(
                rank=index + 1,
                ticker=item.get("ticker", candidate_summaries[index]["ticker"] if index < len(candidate_summaries) else "UNKNOWN"),
                company_name=item.get("company_name", ""),
                rationale=item.get("rationale", ""),
                supporting_signals=item.get("supporting_signals", []),
            )
            for index, item in enumerate(ranked_items)
        ]

        answer = llm_response.get("answer") or self._fallback_field_answer(request, ranked_stocks)
        return FieldAnalysisResponse(
            field=request.field,
            top_x=request.top_x,
            past_days=request.past_days,
            answer=answer,
            ranked_stocks=ranked_stocks,
            retrieved_context=retrieved_context,
            tool_calls=tool_calls,
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
        memory_data = observations.get("memory_search", {})
        price_data = observations.get("get_stock_price", {}) or observations.get("stock_price", {})
        news_data = observations.get("get_stock_news", {}) or observations.get("stock_news", {})

        current_price = price_data.get("current_price", "n/a")
        move_pct = price_data.get("day_change_percent", "n/a")
        headlines = [article.get("title") for article in news_data.get("articles", []) if article.get("title")]
        news_summary = "; ".join(headlines[:2]) if headlines else "No recent headlines were available."
        context_summary = context[0] if context else "No local reference context matched strongly enough to include."
        prior_memory = memory_data.get("items", [])
        memory_summary = prior_memory[0]["content"] if prior_memory else "No relevant prior memory was available."

        return (
            f"For {request.ticker.upper()}, the agent sees a current price near {current_price} "
            f"with a daily move of {move_pct}%. "
            f"Question focus: {request.question} "
            f"Recent signal summary: {news_summary} "
            f"Relevant local context: {context_summary} "
            f"Prior memory: {memory_summary}"
        )

    def _build_field_analysis_prompt(self, payload: dict[str, object]) -> str:
        return (
            "You are a stock analysis assistant running locally with Mistral. "
            "Rank the strongest stocks in the requested field based on the provided stock snapshots, recent headlines, "
            "and retrieved background context. Focus on recent catalysts, momentum, and field relevance. "
            "Return strict JSON with this shape: "
            '{"answer":"string","ranked_stocks":[{"ticker":"string","company_name":"string","rationale":"string","supporting_signals":["string"]}]}. '
            "Do not include markdown.\n\n"
            f"INPUT:\n{json.dumps(payload, indent=2)}"
        )

    def _fallback_field_answer(self, request: FieldAnalysisRequest, ranked_stocks: list[RankedStock]) -> str:
        if not ranked_stocks:
            return f"No ranked stocks were produced for {request.field}."
        tickers = ", ".join(stock.ticker for stock in ranked_stocks)
        return f"Top {request.top_x} stocks in {request.field} over the past {request.past_days} days: {tickers}."
