#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

if [ ! -d "${VENV_DIR}" ]; then
  echo "Virtual environment not found. Running build first."
  "${ROOT_DIR}/build.sh"
fi

source "${VENV_DIR}/bin/activate"

if ! python -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  echo "Dependencies are missing. Running build first."
  "${ROOT_DIR}/build.sh"
  source "${VENV_DIR}/bin/activate"
fi

if [ -f "${ROOT_DIR}/.env" ]; then
  echo "Using environment from ${ROOT_DIR}/.env"
elif [ -f "${ROOT_DIR}/.env.example" ]; then
  echo "Tip: copy .env.example to .env if you want custom configuration."
fi

echo "Starting Stock Analysis Agent at http://${HOST}:${PORT}"
exec uvicorn main:app --host "${HOST}" --port "${PORT}" --reload
