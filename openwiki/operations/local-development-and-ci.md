---
type: development and continuous-integration operations
title: Local Development, Services, and CI
description: Safe operating guidance for local configuration, Docker-backed PostgreSQL and Qdrant, the P0 and chat UI development pair, workspace checks, CI gates, and the independent OpenWiki refresh workflow.
tags: [operations, local-development, docker, postgresql, qdrant, ci, github-actions, openwiki]
verified:
  - by: openwiki/0.4.3
    at: 2026-08-29T08:58:08.509Z
sources:
  - id: openwiki-source-5f5b95b3d6a215fa02ceb945
    resource: repo://.env.example
  - id: openwiki-source-164e2da859b5277df81c7d94
    resource: repo://.github/workflows/ci.yml
  - id: openwiki-source-6d4b4e707b8d60b6ccfa3425
    resource: repo://.github/workflows/openwiki-update.yml
  - id: openwiki-source-ea70eb6c045047448e446296
    resource: repo://.gitignore
  - id: openwiki-source-8037e2358a2c4f9b2c722a11
    resource: repo://AGENTS.md
  - id: openwiki-source-0f034b4ca648b1c010cda39b
    resource: repo://agents/P0-smoke/src/P0_smoke/server.py
  - id: openwiki-source-a5eee5d995083886549ed8a4
    resource: repo://agents/P0-smoke/tests/test_agent.py
  - id: openwiki-source-76b2c7ba05ee64debdb9e042
    resource: repo://agents/P0-smoke/tests/test_server.py
  - id: openwiki-source-77527f2b28fede553a301ac8
    resource: repo://apps/chat-ui/.env.example
  - id: openwiki-source-6bb2ed781138799a315f6a72
    resource: repo://apps/chat-ui/app/api/health/route.ts
  - id: openwiki-source-8fafd494de7a0c44216791ba
    resource: repo://apps/chat-ui/next.config.ts
  - id: openwiki-source-dde7506bbedc3b760b99cb12
    resource: repo://apps/chat-ui/tests/api.test.ts
  - id: openwiki-source-31ad05e5fb1552f6f5d7614e
    resource: repo://common/src/common/config.py
  - id: openwiki-source-701dfbe923db9f34b48d1b7e
    resource: repo://common/src/common/llm.py
  - id: openwiki-source-4663c0c0ddc822cb6e7dfb1d
    resource: repo://common/tests/test_config.py
  - id: openwiki-source-2480eda4770a7db2844a2087
    resource: repo://docker/.env.example
  - id: openwiki-source-5be27729131e30130689f927
    resource: repo://docker/docker-compose.yml
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

## Operating model

The implemented local foundation is a Python `uv` workspace plus two independently started processes: the P0 FastAPI agent on port `8000` and the Next.js chat UI on port `3000`. Docker Compose supplies PostgreSQL and Qdrant as reusable local dependencies, but P0 is a streaming model smoke test and does not itself read or write either store. The UI proxies its relative `/v1/*` requests to the configured agent origin, which defaults to P0 at `http://localhost:8000`.

This separation is intentional: bring up Docker services when developing or testing work that needs durable or vector infrastructure, start the agent and UI separately for an interactive P0 check, and stop the Compose stack explicitly when it is no longer needed. The root pytest configuration labels service-dependent tests as `integration` and model-calling tests as `eval`; normal repository commands exclude the costly/provider-dependent `eval` tests but do not exclude `integration` tests.

```mermaid
flowchart TD
    Config["Copy local env templates"] --> Sync["uv sync"]
    Sync --> Services["bash scripts/dev-up.sh"]
    Services --> Ready{"Postgres healthy and Qdrant healthz responds"}
    Ready -- "yes" --> P0["P0 Uvicorn on port 8000"]
    P0 --> UI["Next.js chat UI on port 3000"]
    UI --> Proxy["Rewrite relative /v1 requests"]
    Proxy --> P0
    Ready -- "no after 30 seconds" --> Diagnose["Inspect docker compose ps"]
    UI --> StopUI["Stop UI process"]
    P0 --> StopP0["Stop P0 process"]
    Services --> Down["bash scripts/dev-down.sh"]
```

*The local lifecycle: configure, synchronize, health-check the shared services, run the two application processes, then stop each process and the Compose stack deliberately.*

## Configure from non-secret templates

Start from the tracked examples, never by sharing or committing a populated local environment file:

```bash
cp .env.example .env
cp docker/.env.example docker/.env
cp apps/chat-ui/.env.example apps/chat-ui/.env.local
```

The repository ignores `.env`, `.env.local`, `*.env.*.local`, and `docker/.env` while retaining `.env.example`; treat the generated files as local secrets/configuration. Do not paste API keys into source, tests, issue comments, streamed tool payloads, or logs.

### Root process configuration: `.env`

The root `.env.example` is the template for model-provider and LangSmith values:

| Purpose | Template variables | Operational note |
| --- | --- | --- |
| Model credentials | `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_CLOUD_API_KEY` | Current P0 selects the `reasoning` route, which requires `OPENROUTER_API_KEY`. The shared factory currently uses OpenRouter for non-`local` routes and Ollama Cloud for `local`; merely having a direct Anthropic or OpenAI placeholder does not enable a direct client route. |
| Tracing | `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_ENDPOINT`, `LANGSMITH_PROJECT_PREFIX` | Settings default tracing to enabled and compose project names as `<prefix>/<agent-slug>`, normally `LearnAgenticAI/P0-smoke`. The tracing scope only puts `LANGSMITH_API_KEY` in the environment when it is nonempty. |

`common.config.Settings` reads the repository-root `.env` and environment variables case-insensitively, ignores extra variables, and `get_settings()` caches one settings object. Configure values before launching a process. If a test deliberately changes environment variables, it must clear `get_settings.cache_clear()` before using a consumer that calls the accessor; changing a file or shell variable does not refresh an already-running server.

Missing credentials fail at model construction with an actionable `RuntimeError`: `OPENROUTER_API_KEY` for P0's route, or `OLLAMA_CLOUD_API_KEY` for the `local` route. That is preferable to diagnosing a remote request failure after the stream is established.

### Docker service configuration: `docker/.env`

`docker/.env.example` contains intentionally local defaults:

```text
POSTGRES_USER=agentic
POSTGRES_PASSWORD=agentic
POSTGRES_DB=agentic
POSTGRES_PORT=5432
QDRANT_PORT=6333
```

Use different values or host ports if the defaults conflict with another local stack. The Compose file falls back to the same values when variables are absent. `scripts/dev-up.sh` creates `docker/.env` from this example if it does not exist, then sources it so its host-side Qdrant health check uses the same configured port as Compose.

The shared Python settings currently default to `postgresql://agentic:agentic@localhost:5432/agentic` and `http://localhost:6333`. If local Compose credentials or ports are changed, set the consuming process's `DATABASE_URL` and/or `QDRANT_URL` consistently; the Docker template itself does not rewrite the root process settings.

### UI backend selection: `apps/chat-ui/.env.local`

The UI template sets:

```text
NEXT_PUBLIC_AGENT_BASE_URL=http://localhost:8000
```

Next.js rewrites `/v1/:path*` to `${NEXT_PUBLIC_AGENT_BASE_URL}/v1/:path*`, with `http://localhost:8000` as its code fallback. Set this variable to another compatible agent origin when substituting P0, then restart the Next development server so it reads the changed configuration. The UI health endpoint, `GET /api/health`, only confirms that the Next.js shell is up; it does not probe the selected agent, model provider, PostgreSQL, or Qdrant.

## Boot and verify PostgreSQL and Qdrant

From the repository root, install the workspace and start services:

```bash
uv sync
bash scripts/dev-up.sh
```

`uv sync` resolves the root workspace, whose members are `common` and `agents/*`; the supported Python range is `>=3.11,<3.13`. `dev-up.sh` changes into `docker/` and runs `docker compose up -d`, starting these containers and named storage locations:

| Service | Image and host exposure | Persistence and readiness |
| --- | --- | --- |
| PostgreSQL | `postgres:16-alpine`; `${POSTGRES_PORT:-5432}:5432` | Uses named volume `postgres-data`. Compose runs `pg_isready -U <user> -d <database>` every five seconds, with a five-second timeout and five retries. |
| Qdrant | `qdrant/qdrant:v1.12.0`; `${QDRANT_PORT:-6333}:6333` | Uses named volume `qdrant-data`; configures internal gRPC port `6334`. The provided Compose definition does not declare a Qdrant container healthcheck. |

The startup script is the authoritative combined readiness gate. For up to 30 one-second attempts, it requires **both** PostgreSQL's Compose-reported `healthy` status and a successful `curl -fs http://localhost:${QDRANT_PORT:-6333}/healthz`. On success it exits zero; on timeout it prints `docker compose ps` and exits nonzero. Do not start a service-dependent agent immediately after `docker compose up -d` without waiting for this gate or performing equivalent checks.

Useful manual checks after a failure are:

```bash
cd docker
docker compose ps
curl -fs http://localhost:${QDRANT_PORT:-6333}/healthz
```

A Postgres failure is commonly a port conflict, bad changed credentials, or an unhealthy initialized volume; a Qdrant failure is commonly a port conflict or a process not yet listening. The script's final status output identifies the Compose-side state, while the Qdrant `curl` check establishes HTTP reachability from the host.

Stop the stack from any directory with:

```bash
bash scripts/dev-down.sh
```

The script enters `docker/` and runs `docker compose down`. It does not pass `--volumes`; handle any destructive volume removal as a separate, intentional operation rather than assuming ordinary development shutdown wipes local state.

## Run the P0 and UI pair

P0 is the reference backend for the UI contract. It accepts `POST /v1/chat/completions`, requires a nonempty message list, streams `text/event-stream`, and uses P0's `reasoning` model route. Make `OPENROUTER_API_KEY` available in the root `.env` before using it interactively. LangSmith configuration is useful for tracing but does not replace the model key required by the P0 route.

In one terminal, from the repository root:

```bash
cd agents/P0-smoke
uv run uvicorn P0_smoke.server:app --reload --port 8000
```

In another terminal:

```bash
cd apps/chat-ui
pnpm install
pnpm dev
```

Open http://localhost:3000 and send a message. The browser posts to the UI's relative `/v1/chat/completions` path; the rewrite forwards it to P0. A normal P0 stream emits zero or more `token` events, then `message_end`, then `trace_meta`; a stream-time exception becomes an in-band `error` event with code `agent_exception` rather than a replacement HTTP response. This matters during diagnosis: an HTTP 422 indicates invalid input rejected before streaming, whereas a visible inline error in the assistant message indicates a failure after the SSE response began.

For an end-to-end operational check, verify all of the following rather than relying only on the UI page loading:

1. `bash scripts/dev-up.sh` completes successfully if the work needs shared infrastructure.
2. The P0 terminal shows Uvicorn listening on port `8000` and the UI loads at http://localhost:3000.
3. One submitted prompt progressively renders text, proving the UI rewrite, P0 route, provider credential, and SSE path work together.
4. When tracing is configured, the completed response includes a trace link. P0 generates a UUID locally for that metadata and constructs `https://smith.langchain.com/r/<uuid>`; it is UI metadata, not proof that LangSmith issued or has stored a run with that identifier.

Stop the foreground Uvicorn and Next.js processes with their terminal interrupt, then run `bash scripts/dev-down.sh` if the Docker dependencies are no longer required.

## Workspace checks and focused tests

The root workspace owns Python dependency resolution and discovery. Run the repository's normal local suite with:

```bash
bash scripts/test.sh
```

The script runs:

```bash
uv run pytest -v -m "not eval"
(cd apps/chat-ui && pnpm test)
```

The Python command discovers `common/tests` and `agents/*/tests`. It intentionally excludes tests marked `eval`, because those tests call a real LLM API and can be slow or incur cost. It does not exclude the `integration` marker, which the project defines for tests requiring Docker PostgreSQL/Qdrant; bring up services first when such tests exist or are selected. The UI portion runs Vitest if `apps/chat-ui` exists.

Use narrower checks while changing a boundary:

```bash
uv run pytest -v -m "not eval"
uv run --package common ruff check common/src common/tests
uv run --package P0-smoke ruff check agents/P0-smoke/src agents/P0-smoke/tests
uv run --package common mypy common/src
uv run --package P0-smoke mypy agents/P0-smoke/src
cd apps/chat-ui && pnpm typecheck && pnpm lint && pnpm test
```

The most valuable offline contract coverage is in `common`: settings defaults/overrides/cache behavior, task routing and missing-key errors, LangSmith environment restoration, and exact SSE framing/payloads. P0's malformed-request tests assert 422 without contacting a provider. Its well-formed endpoint stream test and agent invocation/stream tests are `eval`-marked because consuming them reaches the live model. The current UI Vitest test checks only `GET /api/health`; it is not a substitute for manually exercising the streaming proxy or for adding deterministic UI stream tests when that client code changes.

## CI quality gates

`.github/workflows/ci.yml` is the merge-facing quality workflow. It runs on pushes to `main` and `foundation`, pull requests targeting `main`, and manual dispatch. It has independent Python and TypeScript jobs, so a passing UI job does not establish Python correctness and vice versa.

| Job | Environment and dependency policy | Gates |
| --- | --- | --- |
| `Python (uv + pytest + ruff + mypy)` | Ubuntu; `astral-sh/setup-uv@v3`; `uv sync --all-packages --all-extras` | Ruff checks for `common` and `P0-smoke`; strict mypy checks for their `src` trees; `uv run pytest -v -m "not eval"`; Ruff format checks for sources and tests. |
| `TypeScript (Next.js chat UI)` | Ubuntu in `apps/chat-ui`; pnpm plus Node `20`; `pnpm install --frozen-lockfile` with the UI lockfile cache | `pnpm typecheck`, `pnpm lint`, and `pnpm test`. |

CI does not run the `eval` suite, so it does not require a provider key and cannot certify live model behavior. Its Python workflow configuration also does not provision Docker service containers; do not add a required integration test and assume the existing job will start PostgreSQL/Qdrant. Extend the workflow deliberately with service setup or keep that test out of the default CI selection, according to the desired gate.

Before opening a change that affects these paths, run the relevant gates locally. In particular, a Python source or formatting change needs both lint/type/format validation; an SSE protocol change needs the common tests plus coordinated UI verification; and a UI dependency change must preserve the lockfile because CI installs with `--frozen-lockfile`.

## Separately scheduled OpenWiki updates

The OpenWiki workflow is documentation maintenance, not an application CI quality gate. `.github/workflows/openwiki-update.yml` runs only on manual dispatch and the daily cron `0 8 * * *`; it is not triggered by ordinary pushes or pull requests. It has `contents: write` and `pull-requests: write` permissions because it creates a documentation pull request rather than merging generated changes directly.

```mermaid
flowchart TD
    Trigger["Manual dispatch or daily schedule"] --> Checkout["Checkout full Git history"]
    Checkout --> Install["Install Node 22 and OpenWiki tooling"]
    Install --> Update["openwiki code --update --print"]
    Update --> PR["Create or update openwiki/update pull request"]
    PR --> Paths["Commit only documented update paths"]
```

*The independent documentation refresh flow, from scheduled/manual trigger through an update command to a reviewable pull request.*

The workflow checks out with `fetch-depth: 0`. Full history is required because `openwiki code --update` compares `HEAD` with the commit last documented; a shallow checkout would hide that commit and yield an empty change summary. It installs Node `22`, `openwiki@0.4.3`, `mermaid@11.16.0`, and `jsdom@29.1.1`, then runs:

```bash
openwiki code --update --print
```

Its environment selects `OPENWIKI_PROVIDER: openai-chatgpt` and `OPENWIKI_MODEL_ID: "gpt-5.6-terra"`. The workflow comment notes that browser-login authentication has no unattended equivalent, so operators must provide appropriate CI credentials. The LangSmith connector receives `OPENWIKI_LANGSMITH_API_KEY` from the `OPENWIKI_LANGSMITH_API_KEY` repository secret; optional tracing of the documentation run uses `LANGSMITH_API_KEY` from its separate secret along with `LANGCHAIN_PROJECT: openwiki` and `LANGCHAIN_TRACING_V2: "true"`.

Finally, `peter-evans/create-pull-request` creates or updates branch `openwiki/update` with the `docs: update OpenWiki` commit/title. Its explicit allowlist is `openwiki`, `AGENTS.md`, `CLAUDE.md`, and `.github/workflows/openwiki-update.yml`. Review that PR like any other generated documentation change, especially claims tied to code and diagrams. Source and tests remain authoritative; AGENTS.md describes the wiki as optional just-in-time context and directs maintainers not to hand-edit generated pages unless explicitly asked.
