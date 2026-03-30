# Stock Analysis Agent

A local-first stock analysis agent built from the provided spec:

- FastAPI service
- MCP-style tool layer
- Lightweight RAG pipeline
- ReAct-style reasoning loop
- Token-budget-aware prompt construction

## Project Layout

```text
stock_agent/
├── app/
│   ├── agent/
│   ├── api/
│   ├── core/
│   ├── rag/
│   ├── schemas/
│   └── tools/
├── data/knowledge/
├── tests/
└── main.py
```

## Quick Start

```bash
cd stock_agent
./build.sh
./run_local.sh
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Analyze a ticker:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "question": "Should I monitor this stock for near-term catalysts?"
  }'
```

## Configuration

Environment variables:

- `STOCK_AGENT_APP_NAME`
- `STOCK_AGENT_ENV`
- `STOCK_AGENT_TOOL_MODE` (`mock` or `live`)
- `STOCK_AGENT_NEWS_API_KEY`
- `STOCK_AGENT_FINNHUB_API_KEY`
- `STOCK_AGENT_MAX_ITERATIONS`
- `STOCK_AGENT_RAG_TOP_K`
- `STOCK_AGENT_CONTEXT_CHAR_BUDGET`

The default setup uses mock market data so the service works without API keys.

## Local Scripts

- `./build.sh`: creates `.venv`, upgrades packaging tools, and installs project dependencies.
- `./run_local.sh`: ensures the environment is ready and starts the FastAPI app with auto-reload.

## Notes

- The RAG implementation is intentionally lightweight and local. It uses simple token-overlap embeddings so the project runs without heavyweight vector DB dependencies.
- The tool layer is structured so you can later swap in real MCP servers or external providers with minimal changes.
