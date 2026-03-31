# Stock Analysis Agent

A local-first stock analysis agent built from the provided spec:

- FastAPI service
- MCP server with memory
- CNBC-backed tooling via `ycnbc` for quotes and a direct CNBC fetcher for news
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
./scripts/build.sh
./scripts/run_local.sh
```

The MCP tools fetch quote data from CNBC through the `ycnbc` package and fetch stock news directly from CNBC quote pages. If either fetch path fails, the tools fall back to mock responses with a warning in the payload.

Health check:

```bash
curl http://127.0.0.1:8010/health
```

Analyze a ticker:

```bash
curl -X POST http://127.0.0.1:8010/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "AAPL",
    "question": "Should I monitor this stock for near-term catalysts?"
  }'
```

Analyze the top stocks in a field:

```bash
curl -X POST http://127.0.0.1:8010/api/v1/analyze/field \
  -H "Content-Type: application/json" \
  -d '{
    "field": "tech",
    "top_x": 3,
    "past_days": 7,
    "question": "Which stocks look strongest in this field and why?"
  }'
```

The field analysis flow now uses:

- latest snapshot tools: `get_stock_price`, `get_stock_news`
- trailing-window tools: `get_stock_price_history`, `get_stock_news_history`
- Chroma retrieval for field-specific background context
- Mistral on Ollama for final ranking and rationale

Run the standalone MCP server:

```bash
./scripts/run_mcp.sh
curl http://127.0.0.1:8001/info
curl http://127.0.0.1:8001/tools
curl http://127.0.0.1:8001/quote/AAPL
curl "http://127.0.0.1:8001/news/AAPL?company_name=Apple&max_items=3"
```

## Configuration

Environment variables:

- `STOCK_AGENT_APP_NAME`
- `STOCK_AGENT_ENV`
- `STOCK_AGENT_TOOL_MODE` (`ycnbc` or `mock`)
- `STOCK_AGENT_MAX_ITERATIONS`
- `STOCK_AGENT_RAG_TOP_K`
- `STOCK_AGENT_CONTEXT_CHAR_BUDGET`

The default setup uses `ycnbc`, which does not require API keys. Set `STOCK_AGENT_TOOL_MODE=mock` if you want deterministic offline behavior.

## Local Scripts

- `./scripts/build.sh`: creates `.venv` with `uv` and syncs project dependencies.
- `./scripts/run_local.sh`: ensures the uv environment is ready and starts the FastAPI app.
- `./scripts/run_mcp.sh`: starts the standalone MCP service for isolated testing.
- `./scripts/start_chromadb.sh`: starts the Chroma docker container on `localhost:8000`.

## Chroma RAG Ingestion

The Chroma ingestion pipeline writes sector and company knowledge into the Chroma server at `http://localhost:8000`, using Ollama embeddings by default.

The Python app does not run an embedded Chroma database. It talks to the external Chroma server over HTTP, and persistence lives in Docker now and can later move to Chroma Cloud.

Modules:

- [app/rag/fetcher.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/rag/fetcher.py): fetch local files or URLs
- [app/rag/parser.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/rag/parser.py): clean and normalize text
- [app/rag/chunker.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/rag/chunker.py): split text into overlapping chunks
- [app/rag/embedder.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/rag/embedder.py): call Ollama embeddings
- [app/rag/store.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/rag/store.py): write embeddings into Chroma
- [app/rag/ingest.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/rag/ingest.py): CLI entrypoint

Example with direct sources:

```bash
uv run python -m app.rag.ingest \
  --source data/knowledge/market_framework.md \
  --field tech \
  --collection stock-knowledge
```

Example with a manifest:

```bash
uv run python -m app.rag.ingest \
  --sources-file data/knowledge/sources.example.json \
  --collection stock-knowledge
```

Verify what has been ingested:

```bash
uv run python -m app.rag.verify --collection stock-knowledge --limit 10
```

Retrieve chunks from Chroma:

```bash
uv run python -m app.rag.query \
  --collection stock-knowledge \
  --query "best tech stocks and sector catalysts" \
  --field tech \
  --top-k 3
```

You can also call the HTTP API:

```bash
curl "http://127.0.0.1:8010/api/v1/rag/verify?limit=10"
curl -X POST "http://127.0.0.1:8010/api/v1/rag/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"query":"best tech stocks and sector catalysts","field":"tech","top_k":3}'
```

Defaults:

- Ollama URL: `http://localhost:11434`
- Embedding model: `embeddinggemma`
- Chroma host: `localhost`
- Chroma port: `8000`

Python and environment management:

- This project is `uv`-managed.
- Python `3.11` is the expected project version because `chromadb` depends on packages that do not support Python 3.9.
- Chroma access is client-server only. The project uses the lightweight `chromadb-client` package as an HTTP client, not an embedded local database.
- Recommended setup:

```bash
uv python list
uv venv --python 3.11
uv sync --extra dev
```

## Notes

- The RAG implementation is intentionally lightweight and local. It uses simple token-overlap embeddings so the project runs without heavyweight vector DB dependencies.
- The MCP layer now has its own FastAPI app and entrypoint, so you can test tools and memory independently before wiring it into the main stock-agent API.
- The MCP server uses a single MCP-native tools surface, including `get_stock_price` and `get_stock_news`.
- The quote integration is wrapped by a normalization adapter in [app/tools/ycnbc_client.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/tools/ycnbc_client.py).
- The news integration is implemented in [app/tools/cnbc_news_client.py](/Users/zihanchen/local_dev/agent_study/stock_agent/app/tools/cnbc_news_client.py) and uses direct CNBC page fetching with multiple extraction strategies.
