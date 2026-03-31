#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

echo "Project root: ${ROOT_DIR}"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is not installed." >&2
  exit 1
fi

echo "Creating or updating uv virtual environment with Python ${PYTHON_VERSION}"
uv venv --python "${PYTHON_VERSION}" "${ROOT_DIR}/.venv"

echo "Syncing project dependencies"
uv sync --project "${ROOT_DIR}" --extra dev

echo "uv build completed successfully."
