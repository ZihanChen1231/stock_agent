#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8001}"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed." >&2
  exit 1
fi

if [ ! -d "${ROOT_DIR}/.venv" ]; then
  echo "Virtual environment not found. Running build first."
  "${ROOT_DIR}/scripts/build.sh"
fi

if ! uv run --project "${ROOT_DIR}" python -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Dependencies are missing. Running build first."
  "${ROOT_DIR}/scripts/build.sh"
fi

echo "Starting MCP server at http://${HOST}:${PORT}"
exec uv run --project "${ROOT_DIR}" uvicorn app.mcp.api:app --host "${HOST}" --port "${PORT}" --reload
