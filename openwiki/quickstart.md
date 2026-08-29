---
type: contributor guide
title: LearnAgenticAI Quickstart
description: Start here to orient yourself in the LearnAgenticAI workspace, run the implemented P0 streaming chat slice, and route changes to the relevant contracts, operations, workflow, and verification guidance.
tags: [quickstart, contributors, p0, streaming, architecture]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T08:58:08.509Z
sources:
  - id: openwiki-source-5f5b95b3d6a215fa02ceb945
    resource: repo://.env.example
  - id: openwiki-source-164e2da859b5277df81c7d94
    resource: repo://.github/workflows/ci.yml
  - id: openwiki-source-436340c3c693234d9f9a177b
    resource: repo://agents/P0-smoke/pyproject.toml
  - id: openwiki-source-d79516eee108cc2e7e9f3a6d
    resource: repo://agents/P0-smoke/src/P0_smoke/agent.py
  - id: openwiki-source-0f034b4ca648b1c010cda39b
    resource: repo://agents/P0-smoke/src/P0_smoke/server.py
  - id: openwiki-source-76b2c7ba05ee64debdb9e042
    resource: repo://agents/P0-smoke/tests/test_server.py
  - id: openwiki-source-77527f2b28fede553a301ac8
    resource: repo://apps/chat-ui/.env.example
  - id: openwiki-source-6bb2ed781138799a315f6a72
    resource: repo://apps/chat-ui/app/api/health/route.ts
  - id: openwiki-source-0cbafcf980e40aee15cf4097
    resource: repo://apps/chat-ui/components/ChatWindow.tsx
  - id: openwiki-source-c4df2e652c3cabd712770c4e
    resource: repo://apps/chat-ui/components/MessageBubble.tsx
  - id: openwiki-source-f8db607d3b37e59300a0c6f2
    resource: repo://apps/chat-ui/lib/api.ts
  - id: openwiki-source-8fafd494de7a0c44216791ba
    resource: repo://apps/chat-ui/next.config.ts
  - id: openwiki-source-dde7506bbedc3b760b99cb12
    resource: repo://apps/chat-ui/tests/api.test.ts
  - id: openwiki-source-31ad05e5fb1552f6f5d7614e
    resource: repo://common/src/common/config.py
  - id: openwiki-source-701dfbe923db9f34b48d1b7e
    resource: repo://common/src/common/llm.py
  - id: openwiki-source-e0fb919d4f49bf7d07cc6ea8
    resource: repo://common/src/common/tracing.py
  - id: openwiki-source-81bc744f96fdc161bc956665
    resource: repo://common/src/common/ui_bridge.py
  - id: openwiki-source-efb9678b6232d8fedb9f43dc
    resource: repo://common/tests/test_llm.py
  - id: openwiki-source-e09924c35c4510a0c3a45278
    resource: repo://common/tests/test_tracing.py
  - id: openwiki-source-5090e4441b7b1b8b9ff8d2a6
    resource: repo://common/tests/test_ui_bridge.py
  - id: openwiki-source-5be27729131e30130689f927
    resource: repo://docker/docker-compose.yml
  - id: openwiki-source-2ab903dbf99d7df177697f5e
    resource: repo://docs/superpowers/specs/2026-08-28-10-agentic-projects-design.md
  - id: openwiki-source-05ccef8d4cf1698187f20464
    resource: repo://pyproject.toml
  - id: openwiki-source-23775c3de52f3ab95a13cb8b
    resource: repo://README.md
  - id: openwiki-source-a75d8b30d44ec0abc68aa9e1
    resource: repo://scripts/dev-down.sh
  - id: openwiki-source-9670d5581906a288fd303358
    resource: repo://scripts/dev-up.sh
  - id: openwiki-source-2161525089da862e880baf7a
    resource: repo://scripts/test.sh
generated: { by: "openwiki/0.4.3", at: "2026-08-29T08:58:08.509Z" }
---

# LearnAgenticAI Quickstart

LearnAgenticAI is a Python/TypeScript monorepo intended to grow into a portfolio of ten LangChain/LangGraph/LangSmith projects. **The current implemented vertical slice is P0 only**: a FastAPI smoke agent, reusable `common` package, and Next.js chat shell. P0 calls an LLM using a friendly echo prompt and proves the browser-to-SSE-to-model path; it is not a ReAct agent, RAG system, memory system, or multi-agent implementation.

The documented P1–P10 portfolio is a roadmap, not a statement that those projects or their planned infrastructure are present. In particular, the local Postgres and Qdrant services are foundation infrastructure for later work rather than dependencies of P0's current request path.

## Pick your starting task

| If you need to… | Start here | Then read |
| --- | --- | --- |
| Understand what exists now versus the P1–P10 plan | [Current Foundation and Portfolio Architecture](/openwiki/architecture/current-foundation-and-roadmap.md) | The portfolio design spec and `README.md` |
| Run the P0 browser-to-agent smoke slice | [Run P0 locally](#run-the-p0-slice) | [Streaming Chat Completion Workflow](/openwiki/workflows/chat-completion-stream.md) for the complete lifecycle |
| Add or change an agent backend safely | [Shared Agent Contracts](/openwiki/concepts/shared-agent-contracts.md) | [Chat UI and Agent API Boundary](/openwiki/integrations/chat-ui-agent-boundary.md) |
| Change the FastAPI P0 behavior | [P0 Smoke Agent Backend](/openwiki/systems/p0-smoke-agent.md) | The stream workflow and verification strategy |
| Change model routing, settings, tracing, or SSE events | [Shared Agent Contracts](/openwiki/concepts/shared-agent-contracts.md) | Do not independently change only one producer or consumer |
| Configure services, environment files, or CI | [Local Development, Services, and CI](/openwiki/operations/local-development-and-ci.md) | [Verification Strategy](/openwiki/testing/verification-strategy.md) |
| Choose focused tests or understand which tests call a real model | [Verification Strategy](/openwiki/testing/verification-strategy.md) | `scripts/test.sh` for the default command |

## Repository orientation

The root `pyproject.toml` defines a `uv` workspace containing `common` and `agents/*`, with Python 3.11 through 3.12 supported. The three current runtime ownership areas are:

- `common/` owns reusable typed settings, provider/model construction, temporary LangSmith environment setup, and the shared server-sent-event (SSE) vocabulary.
- `agents/P0-smoke/` owns the implemented FastAPI backend. Its `POST /v1/chat/completions` endpoint validates chat history, converts supported roles to LangChain messages, and streams a P0 response.
- `apps/chat-ui/` owns the reusable Next.js client shell. In development, it rewrites `/v1/*` to `NEXT_PUBLIC_AGENT_BASE_URL` (default `http://localhost:8000`), so browser code can post to the same relative endpoint.

The design roadmap assigns P1–P10 to progressively more capable agent patterns—beginning with ReAct and then covering RAG, memory, orchestration, human approval, MCP, deep research, structured output, evaluation, and deployment. Treat that sequence as intended direction and consult the architecture page before scaffolding a project: only `agents/P0-smoke/` is currently a workspace agent.

## Run the P0 slice

### 1. Prepare dependencies and configuration

From the repository root, install the Python workspace and create local configuration files from their non-secret templates:

```bash
uv sync
cp .env.example .env
cp docker/.env.example docker/.env
cp apps/chat-ui/.env.example apps/chat-ui/.env.local
```

Set `OPENROUTER_API_KEY` in `.env` before sending a P0 request: P0 uses the shared `reasoning` route, which selects `deepseek/deepseek-v4-flash-0731` through OpenRouter and fails clearly if that key is absent. `LANGSMITH_API_KEY` enables authenticated tracing; the shared configuration also supplies `LANGSMITH_TRACING`, endpoint, and project-prefix defaults. Do not commit populated `.env`, `docker/.env`, or `.env.local` files.

`OLLAMA_CLOUD_API_KEY`, the other provider keys, and database/vector-store settings are shared configuration extension points. They are not needed for the P0 reasoning route, but future agents may select the `local`, `tools`, `judge`, or `cheap` routes.

### 2. Start optional local foundation services

Start the Docker services when working on functionality that needs the shared database or vector-store endpoints, or when validating the local foundation:

```bash
bash scripts/dev-up.sh
```

The script creates `docker/.env` if missing, starts Postgres and Qdrant, then waits for Postgres's Compose health status and Qdrant's `/healthz` endpoint; it exits non-zero after 30 seconds if both are not ready. Stop the services with:

```bash
bash scripts/dev-down.sh
```

P0 itself does not query Postgres or Qdrant, so a successful P0 chat needs the backend, UI, and LLM credentials—not these services.

### 3. Start backend and UI in separate terminals

Terminal 1:

```bash
cd agents/P0-smoke
uv run uvicorn P0_smoke.server:app --reload --port 8000
```

Terminal 2:

```bash
cd apps/chat-ui
pnpm install
pnpm dev
```

Open http://localhost:3000 and submit a message. The UI proxy forwards `/v1/chat/completions` to the backend at port 8000 by default. If the backend runs elsewhere, change `NEXT_PUBLIC_AGENT_BASE_URL` in `apps/chat-ui/.env.local` and restart Next.js.

## What a successful P0 request proves

1. The browser adds the user message and an empty assistant message, then POSTs all displayed user/assistant history with `stream: true` to `/v1/chat/completions`.
2. FastAPI requires at least one message and accepts only `system`, `user`, and `assistant` roles. It creates a per-request UUID, converts the history to LangChain messages, and opens a `text/event-stream` response.
3. Within a temporary `LearnAgenticAI/P0-smoke` LangSmith project scope, P0 prepends its own friendly-echo system prompt and streams the shared reasoning model.
4. Each nonempty model chunk becomes a `token` SSE event. On normal completion P0 sends `message_end` and then `trace_meta`; if an exception occurs while producing the stream, it sends an `error` event with code `agent_exception` instead of changing the already-started HTTP response.
5. The UI incrementally appends tokens, associates tool lifecycle events by `call_id` for future agent backends, and renders trace metadata as a LangSmith link. P0 currently emits no tool events. The Stop button aborts the browser fetch; intended client aborts are silent, while other client-side failures are added to the assistant message.

The stream vocabulary is a compatibility boundary, not a P0-private convention: `token`, `tool_start`, `tool_end`, `message_end`, `error`, and `trace_meta` are the closed event types shared by agent backends and the UI. Preserve ordering and payload shapes when extending an agent. The client only yields recognized event names and silently skips malformed JSON, so an uncoordinated new event type will be ignored rather than displayed.

For the request-level sequence, failure paths, event payloads, and client state handling, see [Streaming Chat Completion Workflow](/openwiki/workflows/chat-completion-stream.md). For backend/UI substitution requirements, see [Chat UI and Agent API Boundary](/openwiki/integrations/chat-ui-agent-boundary.md).

## Change boundaries that matter

- **Settings and routing:** `get_settings()` is cached; tests or processes that change environment values must clear the cache before re-resolving it. `get_model()` routes by task rather than project name, uses an explicit output cap of 1024 tokens, falls back to `reasoning` for an unknown task, and rejects missing credentials before a model call. Add an intentional task route rather than hard-coding a provider in an individual agent.
- **Tracing scope:** `setup(slug)` sets the LangSmith environment only for its `with` block and restores the caller's prior environment afterward. Keep model invocation inside that scope if it should be attributed to the agent project.
- **SSE contract:** use the `common.ui_bridge` event helpers. They validate event names and serialize the exact `event: …` / JSON `data: …` SSE framing the UI parser expects. A new event requires a coordinated change to the Python closed set, TypeScript union/guard, UI state handling, and tests.
- **P0 response semantics:** the endpoint always streams, even though its request model has a `stream` field; the non-streaming `invoke()` helper is test-oriented and returns `run_id="not-traced"`. Do not infer OpenAI-compatible non-streaming behavior from that field without implementing and testing it.

## Verify the change you made

Use the smallest relevant check first, then the repository default:

```bash
# Default repository test path: Python tests that do not call an LLM, then UI tests
bash scripts/test.sh
```

The default command excludes `@pytest.mark.eval` tests because those tests make live model calls and may incur cost. Run a targeted test while editing its boundary, for example:

```bash
uv run pytest common/tests/test_ui_bridge.py -v
uv run pytest agents/P0-smoke/tests/test_server.py -v -m "not eval"
cd apps/chat-ui && pnpm test
```

Run eval-marked P0 tests only after configuring credentials and accepting a live provider call:

```bash
uv run pytest agents/P0-smoke/tests -v -m eval
```

CI additionally applies Ruff linting and format checks plus strict mypy checks to `common` and P0, and runs TypeScript type checking, linting, and Vitest for the chat UI. The UI's existing automated coverage is its `GET /api/health` route; protocol and component changes therefore need focused tests rather than relying on health coverage alone. See [Verification Strategy](/openwiki/testing/verification-strategy.md) for the test layers and [Local Development, Services, and CI](/openwiki/operations/local-development-and-ci.md) for operating and CI detail.

## Where to go next

- Build against the existing foundation: [Current Foundation and Portfolio Architecture](/openwiki/architecture/current-foundation-and-roadmap.md)
- Preserve reusable settings, tracing, model, and stream contracts: [Shared Agent Contracts](/openwiki/concepts/shared-agent-contracts.md)
- Work on the P0 FastAPI service: [P0 Smoke Agent Backend](/openwiki/systems/p0-smoke-agent.md)
- Trace the complete browser-to-model lifecycle: [Streaming Chat Completion Workflow](/openwiki/workflows/chat-completion-stream.md)
- Operate local services or inspect CI/OpenWiki automation: [Local Development, Services, and CI](/openwiki/operations/local-development-and-ci.md)
- Select tests and understand live-eval boundaries: [Verification Strategy](/openwiki/testing/verification-strategy.md)
