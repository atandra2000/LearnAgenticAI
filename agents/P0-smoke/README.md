# P0 — Smoke Agent

A minimal LangChain agent that echoes the user's message back. Exists to prove the end-to-end plumbing (FastAPI ↔ chat UI ↔ LangSmith) works before P1 starts.

## What it does

Given a chat message, calls an LLM with a "you are a friendly echo" system prompt and streams the response back via SSE. Every run is traced to LangSmith project `LearnAgenticAI/P0-smoke`.

## Architecture

```
POST /v1/chat/completions
        │
        ▼
  FastAPI handler
        │
        ▼
  common.tracing.setup("P0-smoke") ─── wires LANGSMITH_PROJECT
        │
        ▼
  common.llm.get_model("P0-smoke", task="reasoning")
        │
        ▼
  LangChain ChatOpenAI (OpenRouter → DeepSeek V4 Flash)
        │
        ▼
  SSE stream: token, token, ..., message_end, trace_meta
        │
        ▼
  apps/chat-ui/  (consumes events, renders chat)
```

## Run

```bash
cd /Users/atandrabharati/Projects/LearnAgenticAI
uv sync

# Fill in API keys
cp .env.example .env  # already done
# edit .env: set OPENROUTER_API_KEY and LANGSMITH_API_KEY

# Boot
cd agents/P0-smoke
uv run uvicorn P0_smoke.server:app --reload --port 8000

# In another terminal
cd ../../apps/chat-ui
pnpm dev
```

Then open http://localhost:3000 and send "Hello, agent!"

## Test

```bash
cd agents/P0-smoke
uv run pytest -v
```

## Cost

Per 100 runs (single 50-token response): well under $0.05 with DeepSeek V4 Flash via OpenRouter.
