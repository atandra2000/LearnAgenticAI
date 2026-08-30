# LearnAgenticAI

[![CI](https://github.com/atandra2000/LearnAgenticAI/actions/workflows/ci.yml/badge.svg)](https://github.com/atandra2000/LearnAgenticAI/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg?logo=next.js&logoColor=white)](https://nextjs.org/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3%2B-1C3C3C.svg?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-1C3C3C.svg)](https://langchain-ai.github.io/langgraph/)
[![LangSmith](https://img.shields.io/badge/LangSmith-Observability-FF6B6B.svg)](https://smith.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-grade monorepo portfolio of **10 progressive Agentic AI projects** built on the **LangChain / LangGraph / LangSmith / MCP** stack. Designed as an industry-standard reference architecture covering single-agent ReAct loops, production RAG, cross-session memory, multi-agent supervisor hierarchies, human-in-the-loop (HITL) safety, Model Context Protocol (MCP) integrations, deep autonomous subagents, typed structured outputs, and automated evaluation harnesses.

---

## 🏗️ System Architecture

The monorepo is architected around modular FastAPI agent services, a reusable Next.js 15 chat shell, and a shared Python infrastructure package (`common`) for model routing, streaming telemetry, and evaluation gates.

```
                      ┌────────────────────────────────────────────────────────┐
                      │                 apps/chat-ui (Next.js 15)              │
                      │  • Token-by-token SSE streaming                        │
                      │  • Collapsible Tool Call Inspection Trees              │
                      │  • Direct Deep Links to LangSmith Traces               │
                      └───────────────────────────┬────────────────────────────┘
                                                  │ HTTP POST (SSE stream)
                                                  ▼
                      ┌────────────────────────────────────────────────────────┐
                      │              FastAPI Agent Service (/agents/*)         │
                      │  • /v1/chat/completions (OpenAI-compatible)            │
                      │  • StateGraph Execution & Checkpointing                │
                      │  • Interrupt Handling & Resumption Endpoints           │
                      └─────────────┬───────────────────────────┬──────────────┘
                                    │                           │
                   ┌────────────────┴───────────────┐           │
                   ▼                                ▼           ▼
    ┌─────────────────────────────┐   ┌───────────────────────────┐   ┌───────────────────────────────┐
    │    common.llm               │   │    common.ui_bridge       │   │    common.tracing             │
    │  • Multi-provider routing   │   │  • Typed SSE event codec  │   │  • LangSmith telemetry setup  │
    │  • OpenRouter / Ollama      │   │  • token / tool / trace   │   │  • Scoped project contexts    │
    └──────────────┬──────────────┘   └───────────────────────────┘   └───────────────┬───────────────┘
                   │                                                                  │
                   ▼                                                                  ▼
    ┌─────────────────────────────┐                                   ┌───────────────────────────────┐
    │ LLMs (Claude, GPT-4o, Llama)│                                   │ LangSmith Observability Platform│
    └─────────────────────────────┘                                   └───────────────────────────────┘
```

---

## 🚀 The 10-Project Portfolio Matrix

| Project | Pattern | Core Technologies | Eval & Observability | Status |
| :--- | :--- | :--- | :--- | :--- |
| **[P0: Foundation & Smoke](agents/P0-smoke/)** | Shared Infra Validation | FastAPI, SSE Bridge, Next.js 15, LangSmith | Unit + integration smoke tests | ✅ Completed |
| **[P1: ReAct Research Agent](agents/P1-react-agent/)** | Single-Agent Reasoning | `create_react_agent`, Tavily Search, OpenRouter | 30 multi-hop Q&A benchmark (94.7% recall) | ✅ Completed |
| **P2: Production RAG** | Retrieval & Reranking | Semantic Chunking, Qdrant, Cohere Rerank | Faithfulness & Context-Precision evals | ⏳ Planned |
| **P3: Conversational Memory** | Multi-Tier State Store | LangGraph `MemorySaver` + PostgreSQL Store | 20 multi-turn recall benchmarks | ⏳ Planned |
| **P4: Multi-Agent Supervisor** | Hierarchical Orchestration | LangGraph Subgraphs, `Command` handoffs | 15 collaborative research tasks | ⏳ Planned |
| **P5: HITL Approval Workflow** | Human-in-the-Loop Safety | LangGraph `interrupt()`, Resumable Checkpoints | 10 destructive mutation scenarios | ⏳ Planned |
| **P6: MCP Tool Server** | Protocol-Driven Tooling | Python `mcp` SDK, `langchain-mcp-adapters` | 12 cross-tool workflow evaluations | ⏳ Planned |
| **P7: Deep Research Agent** | Long-Horizon Autonomy | Parallel `Send` API, Context Offloading | LLM-as-a-Judge report rubrics | ⏳ Planned |
| **P8: Structured-Output Agent** | Typed Schema Extraction | Pydantic v2, Retry Prompt Injection | 30 malformed input edge cases | ⏳ Planned |
| **P9: Eval & Observability** | CI/CD Quality Gates | LangSmith `evaluate()`, Trajectory Matching | Meta-evals against human labels | ⏳ Planned |
| **P10: Production Capstone** | Full-Stack Deployment | Docker, FastAPI, Rate Limiting, Sentry | Locust load tests + online evals | ⏳ Planned |

---

## 📂 Repository Structure

```
LearnAgenticAI/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Python (uv, ruff, mypy, pytest) + TypeScript (vitest, typecheck, lint)
│       └── openwiki-update.yml    # Automated documentation synchronization
├── agents/
│   ├── P0-smoke/                  # Smoke validation agent (FastAPI + LangChain)
│   │   ├── src/P0_smoke/          # Server and agent graph implementation
│   │   ├── tests/                 # Unit and integration test suites
│   │   └── pyproject.toml         # Agent package definition
│   ├── P1-react-agent/            # Autonomous ReAct research agent (Tavily + web reading)
│   │   ├── src/P1_react_agent/    # ReAct graph, prompts, and SSE bridge
│   │   ├── data/                  # 30-question multi-hop eval dataset
│   │   ├── tests/                 # Unit, integration, and eval test suites
│   │   ├── eval.py                # Offline evaluation CLI benchmark
│   │   └── pyproject.toml         # Agent package definition
│   └── ...                        # P2 through P10 agent packages
├── apps/
│   └── chat-ui/                   # Next.js 15 chat shell with Tailwind CSS & Lucide icons
│       ├── app/                   # App Router pages and health routes
│       ├── components/            # ChatWindow, ToolCallTree, TraceLink, MessageBubble
│       ├── lib/                   # API streaming client and TypeScript types
│       └── tests/                 # Vitest test suite
├── common/                        # Shared Python workspace package
│   ├── src/common/
│   │   ├── config.py              # Pydantic BaseSettings environment configuration
│   │   ├── llm.py                 # Multi-model factory (OpenRouter, Ollama, OpenAI)
│   │   ├── tracing.py             # LangSmith context manager and telemetry setup
│   │   ├── ui_bridge.py           # Typed SSE event formatters (token, tool, trace)
│   │   └── tools/                 # Shared search, filesystem, and data tools
│   └── tests/                     # Unit tests for shared infrastructure
├── docker/
│   ├── docker-compose.yml         # Local Postgres (pgvector) and Qdrant services
│   └── .env.example               # Docker environment templates
├── docs/                          # Architecture specifications and implementation plans
├── scripts/
│   ├── test.sh                    # Monorepo test runner (Python + TypeScript)
│   ├── dev-up.sh                  # Bootstrap local Docker infrastructure
│   └── dev-down.sh                # Tear down local Docker services
└── pyproject.toml                 # uv monorepo workspace configuration
```

---

## 🛠️ Shared Infrastructure Core Modules

### 1. Unified Multi-Model Routing (`common.llm`)
Route dynamically across LLM providers based on project load and reasoning requirements:

```python
from common.llm import get_model

# High-reasoning agent model
model = get_model(project="P1-react-agent", task="reasoning")

# Cost-optimized evaluator model
eval_model = get_model(project="P2-rag", task="eval")
```

### 2. Scoped LangSmith Telemetry (`common.tracing`)
Isolate project traces cleanly in LangSmith with automatic environment scoping:

```python
from common.tracing import setup

# Automatically configures LANGSMITH_PROJECT="LearnAgenticAI/P1-react-agent"
with setup("P1-react-agent"):
    response = agent.invoke({"messages": [...]})
```

### 3. Typed SSE Streaming Protocol (`common.ui_bridge`)
Format events predictably for consumer frontends:

```python
from common.ui_bridge import to_sse

# Stream individual tokens
yield to_sse("token", {"delta": "Hello"})

# Stream tool start and completion telemetry
yield to_sse("tool_start", {"id": "call_1", "tool": "tavily_search", "args": {"query": "LangGraph"}})
yield to_sse("tool_end", {"id": "call_1", "result": "..."})

# Attach LangSmith trace URL
yield to_sse("trace_meta", {"run_id": "8f2a...", "project": "LearnAgenticAI/P1-react-agent"})
```

---

## ⚡ Quickstart & Local Setup

### Prerequisites
- [uv](https://docs.astral.sh/uv/) (v0.4.0+)
- [Node.js](https://nodejs.org/) (v22+) & [pnpm](https://pnpm.io/) (v9+)
- [Docker](https://www.docker.com/) & Docker Compose

### 1. Environment Setup
```bash
# Clone the repository
git clone git@github.com:atandra2000/LearnAgenticAI.git
cd LearnAgenticAI

# Copy environment configuration files
cp .env.example .env
cp docker/.env.example docker/.env
cp apps/chat-ui/.env.example apps/chat-ui/.env.local

# Edit .env and supply your API keys:
# OPENROUTER_API_KEY=...
# LANGSMITH_API_KEY=...
```

### 2. Install Dependencies & Start Services
```bash
# Sync Python workspace packages
uv sync --all-packages --all-extras

# Install frontend dependencies
pnpm --dir apps/chat-ui install

# Start local backing services (PostgreSQL + Qdrant)
bash scripts/dev-up.sh
```

### 3. Run the Agent & Frontend
In terminal 1 (Backend Agent):
```bash
cd agents/P0-smoke
uv run uvicorn P0_smoke.server:app --reload --port 8000
```

In terminal 2 (Next.js Chat UI):
```bash
pnpm --dir apps/chat-ui dev
```

Open [http://localhost:3000](http://localhost:3000) to interact with the agent.

---

## 🧪 Testing & Verification

The repository enforces strict typing, linting, and automated testing across both Python and TypeScript workspaces.

```bash
# Run the complete test suite (Python pytest + TypeScript vitest)
bash scripts/test.sh

# Python Linting & Formatting
uv run ruff check .
uv run ruff format --check .

# Python Static Type Analysis
uv run mypy common/src agents/P0-smoke/src

# TypeScript Typecheck & Linting
pnpm --dir apps/chat-ui typecheck
pnpm --dir apps/chat-ui lint
```

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.
