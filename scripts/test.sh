#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Python tests (non-eval)"
uv run pytest -v -m "not eval"

if [ -d apps/chat-ui ]; then
  echo "==> TypeScript tests"
  (cd apps/chat-ui && pnpm test)
fi

echo "==> All tests passed"
