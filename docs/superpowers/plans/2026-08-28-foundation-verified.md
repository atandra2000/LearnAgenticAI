# Foundation Plan — Verified

**Date:** 2026-08-29
**Verified by:** Atandra Bharati

## Smoke test results

- [x] `uv sync --all-packages --all-extras` resolves all workspace members
- [x] Postgres + Qdrant healthy via `bash scripts/dev-up.sh`
- [x] 26 tests pass (23 common + 3 P0 server; 4 eval-marked deselected without keys)
- [x] `uv run uvicorn P0_smoke.server:app --port 8000` boots
- [x] `curl /v1/chat/completions` returns SSE in expected wire format
- [x] `pnpm dev` boots chat UI on :3000
- [x] Browser round-trip: tokens stream, trace link appears
- [x] LangSmith project `LearnAgenticAI/P0-smoke` shows a real trace

## Notes from verification

- First live attempt surfaced an OpenRouter 402 (no `max_tokens` sent → OpenRouter
  assumed the model's 64k output budget vs ~21k affordable credits). Fixed in
  `common.llm.get_model` with a `max_tokens=1024` default (`6a223d7`).
- Reasoning route switched from `anthropic/claude-sonnet-4.5` to
  `deepseek/deepseek-v4-flash-0731` by user directive (`9db4b8f`); spec §5's
  routing row amended accordingly.
- The error path was exercised live: an upstream failure rendered as a clean
  `[error: …]` line in the chat bubble via the SSE `error` event.

## Ready to start P1

Foundation is verified. P1 (ReAct Research Agent) can begin.
