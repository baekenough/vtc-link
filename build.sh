#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="vtc-link"
IMAGE_TAG="latest"

if command -v docker >/dev/null 2>&1; then
  docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" .
else
  echo "docker를 찾을 수 없음"
  exit 1
fi
