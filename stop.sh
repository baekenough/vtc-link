#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="vtc-link"
IMAGE_NAME="vtc-link"

if command -v docker >/dev/null 2>&1; then
  docker rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
  docker ps -a --filter "ancestor=${IMAGE_NAME}" --format "{{.ID}}" | xargs -r docker rm -f
else
  echo "docker를 찾을 수 없음"
  exit 1
fi
