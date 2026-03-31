#!/bin/bash
set -euo pipefail

CONTAINER_NAME="chroma-db"
PORT=8000
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${ROOT_DIR}/chroma_data"

echo "Starting ChromaDB..."

mkdir -p "${DATA_DIR}"

if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
  echo "Container already exists. Removing..."
  docker rm -f "${CONTAINER_NAME}"
fi

docker run -d \
  --name "${CONTAINER_NAME}" \
  -p "${PORT}:8000" \
  -v "${DATA_DIR}:/data" \
  chromadb/chroma

echo "ChromaDB started at http://localhost:${PORT}"
