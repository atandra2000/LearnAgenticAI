# LearnAgenticAI

A portfolio of 10 production-grade agentic AI projects built on the LangChain / LangGraph / LangSmith stack. Designed as interview prep for an Agentic AI Engineer role.

## Projects

| #   | Project                        | Pattern                              |
| --- | ------------------------------ | ------------------------------------ |
| P0  | Smoke test                     | Validates the shared infra           |
| P1  | ReAct Research Agent           | Single-agent foundation              |
| P2  | Production RAG                 | Retrieval deep-dive                  |
| P3  | Conversational Agent w/ Memory | Memory patterns                      |
| P4  | Multi-Agent Supervisor         | Orchestration                        |
| P5  | HITL Approval Workflow         | Safety + interrupts                  |
| P6  | MCP-Powered Tool Server        | Protocol integration                 |
| P7  | Deep Research Agent            | Long-horizon autonomy                |
| P8  | Structured-Output Agent        | Typed real-world writes              |
| P9  | Eval & Observability Harness   | Meta-skill                           |
| P10 | Production Deploy Capstone     | Full-stack ship                      |

## Setup

```bash
# 1. Install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install pnpm (if not already)
npm install -g pnpm

# 3. Sync Python workspace
uv sync

# 4. Boot infra (postgres + qdrant)
bash scripts/dev-up.sh

# 5. Copy env templates and fill in
cp .env.example .env
cp docker/.env.example docker/.env
cp apps/chat-ui/.env.example apps/chat-ui/.env.local
# edit each .env with your API keys
```

## Running an agent

```bash
# P0 smoke agent
cd agents/P0-smoke
uv run uvicorn P0_smoke.server:app --reload --port 8000

# In another terminal, the chat UI
cd apps/chat-ui
pnpm install
pnpm dev
```

Then open http://localhost:3000.

## Spec & Plans

- Spec: `docs/superpowers/specs/2026-08-28-10-agentic-projects-design.md`
- Plans: `docs/superpowers/plans/`
