#!/usr/bin/env bash
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  uv sync
  uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "uv를 찾을 수 없음"
  exit 1
fi
