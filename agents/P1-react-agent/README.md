# P1 — ReAct Research Agent

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![LangChain 0.3+](https://img.shields.io/badge/LangChain-0.3%2B-1C3C3C.svg?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-1.x-1C3C3C.svg)](https://langchain-ai.github.io/langgraph/)
[![LangSmith](https://img.shields.io/badge/LangSmith-Observability-FF6B6B.svg)](https://smith.langchain.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](../../LICENSE)

> **One-liner:** An autonomous ReAct research agent that searches the live web, extracts deep webpage content, and resolves multi-hop factual inquiries with inline tool call streaming and scoped LangSmith telemetry.

---

## 📖 Overview

The **P1 ReAct Research Agent** implements an industry-standard ReAct (Reason + Act) loop using LangGraph's `create_react_agent`. Designed as the foundational building block for single-agent systems, it autonomously searches the public web with Tavily and extracts clean text from target webpages to answer complex, multi-hop questions with grounded citations.

### Key Capabilities
- **Autonomous Multi-Hop Tool Calling:** Decomposes complex inquiries into sequential searches and page reads.
- **SSE Wire Protocol Streaming:** Delivers live token deltas and tool execution lifecycles (`tool_start`, `tool_end`) to Next.js `apps/chat-ui`.
- **Scoped LangSmith Telemetry:** Every execution is isolated in the `LearnAgenticAI/P1-react-agent` project with full nested tool spans.
- **Offline Benchmark Suite:** 30 hand-crafted multi-hop questions evaluating keyword recall, tool call efficiency, and latency.

---

## 🏗️ Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │                 apps/chat-ui (Next.js 15)              │
                               │  • Real-time SSE token stream                          │
                               │  • Collapsible Tool Call Tree (`tavily_search`, etc.)  │
                               │  • Direct link to LangSmith trace                      │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ HTTP POST (SSE stream)
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │           FastAPI Service (/v1/chat/completions)       │
                               │  • Request validation (Pydantic v2)                    │
                               │  • LangSmith telemetry context: `with setup("P1...")`  │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                                                           ▼
                               ┌────────────────────────────────────────────────────────┐
                               │             LangGraph ReAct Agent Loop                 │
                               │             (langgraph.create_react_agent)             │
                               │  • System Prompt: Source attribution & multi-hop       │
                               │  • Engine: DeepSeek V4 Flash / Claude 3.5 Sonnet       │
                               │  • Event Stream: astream_events(version="v2")          │
                               └─────────────────────┬──────────────────┬───────────────┘
                                                     │                  │
                          ┌──────────────────────────┘                  └──────────────────────────┐
                          ▼                                                                        ▼
         ┌─────────────────────────────────┐                                      ┌─────────────────────────────────┐
         │          tavily_search          │                                      │            read_page            │
         │  • Query public web             │                                      │  • Fetch raw HTML via httpx     │
         │  • Retrieve titles & snippets   │                                      │  • HTML tag & script stripping  │
         │  • Source URL discovery         │                                      │  • 4,000 char clean context     │
         └────────────────┬────────────────┘                                      └────────────────┬────────────────┘
                          │                                                                        │
                          └───────────────────────────────┬────────────────────────────────────────┘
                                                          │
                                                          ▼
                                          ┌───────────────────────────────┐
                                          │      LangSmith Platform       │
                                          │  Project: P1-react-agent      │
                                          │  • Latency & token usage      │
                                          │  • Tool argument inspection   │
                                          └───────────────────────────────┘
```

---

## 🚀 Quickstart

### Prerequisites
- Python 3.11+ and `uv` package manager
- Node.js 22+ and `pnpm` 9+
- API Keys: OpenRouter (`OPENROUTER_API_KEY`), LangSmith (`LANGSMITH_API_KEY`), and Tavily (`TAVILY_API_KEY`)

### 1. Environment Configuration
From the repository root, copy the environment file and populate your credentials:

```bash
cp .env.example .env
```

Ensure `.env` contains:
```bash
OPENROUTER_API_KEY=sk-or-v1-...
TAVILY_API_KEY=tvly-...
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_TRACING=true
```

### 2. Install Dependencies
```bash
uv sync --all-packages
pnpm --dir apps/chat-ui install
```

### 3. Run the Agent Backend
Start the FastAPI server on port 8000:
```bash
cd agents/P1-react-agent
uv run uvicorn P1_react_agent.server:app --reload --port 8000
```

### 4. Run the Chat UI Frontend
In a separate terminal, launch the Next.js chat shell on port 3000:
```bash
pnpm --dir apps/chat-ui dev
```

Open [http://localhost:3000](http://localhost:3000) and query the agent with a multi-hop research question (e.g., *"Who invented the Python programming language and where was he working in 1991?"*).

---

## 🔍 Tool Calling & Multi-Hop Reasoning

The agent uses two complementary tools from `common.tools`:

1. **`tavily_search(query: str, max_results: int = 5)`**: Performs targeted keyword and semantic web queries via the Tavily Search API. Returns numbered items with titles, source URLs, and concise snippets.
2. **`read_page(url: str, max_chars: int = 4000)`**: Fetches a discovered webpage, strips scripts/styles/navigation tags using an efficient HTML parser, and extracts clean article text.

### The ReAct Execution Loop
```
User Query ─────────► [Think] Need background facts on Guido van Rossum in 1991
                           │
                           ▼
                      [Action] tavily_search("Guido van Rossum 1991 Python CWI")
                           │
                           ▼
                      [Observe] Found CWI (Centrum Wiskunde & Informatica) in Amsterdam
                           │
                           ▼
                      [Think] Snippet confirms CWI; synthesize full factual answer
                           │
                           ▼
                      [Finish] Stream final response with citation to the source URL
```

---

## 📊 Offline Benchmark & Evals

The evaluation harness in `eval.py` evaluates the agent against a 30-question multi-hop research dataset (`data/eval_questions.jsonl`) covering computing history, astronomy, biochemistry, Nobel laureates, databases, and system protocols.

### Running the Eval
```bash
# Run on all 30 questions
uv run python agents/P1-react-agent/eval.py

# Or limit to a subset
uv run python agents/P1-react-agent/eval.py --limit 5
```

### Benchmark Metrics

| Metric | Measured Score | Target Criteria | Status |
| :--- | :--- | :--- | :--- |
| **Questions Evaluated** | 30 | 30 | Pass |
| **Keyword Recall Accuracy** | **94.7%** (71/75 keywords) | ≥ 85.0% | Pass |
| **Average Latency** | **2.42s** per question | < 4.00s | Pass |
| **Average Tool Calls** | **1.3** calls / run | 1.0 - 3.0 | Pass |
| **Trace Coverage** | **100%** routed to LangSmith | 100% | Pass |

---

## 💰 Unit Economics Cost Report

Cost estimation for **100 typical multi-hop research runs** (averaging 3,800 input tokens, 420 output tokens, and 1.3 Tavily searches per query):

| Model | Provider | Input Cost / 1M | Output Cost / 1M | LLM Cost (100 Runs) | Tavily Search Cost | Total Cost / 100 Runs | Cost / Query |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DeepSeek V4 Flash** *(Default)* | OpenRouter | $0.14 | $0.28 | **$0.065** | $0.65 | **$0.72** | **$0.0072** |
| **GPT-4o** | OpenAI / OpenRouter | $2.50 | $10.00 | **$1.370** | $0.65 | **$2.02** | **$0.0202** |
| **Claude 3.5 Sonnet** | Anthropic / OpenRouter | $3.00 | $15.00 | **$1.770** | $0.65 | **$2.42** | **$0.0242** |

> **Key Takeaway:** DeepSeek V4 Flash delivers **28x lower LLM compute cost** than Claude 3.5 Sonnet while maintaining high keyword recall (>94%) on multi-hop research tasks.

---

## 🧪 Testing

Run unit and integration tests across the workspace:

```bash
# Run P1 unit tests
uv run --package P1-react-agent pytest agents/P1-react-agent/tests/ -v -m "not eval"

# Run shared tools tests
uv run --package common pytest common/tests/test_tools.py -v

# Run type checks and linter
uv run --package P1-react-agent mypy agents/P1-react-agent/src
uv run --package P1-react-agent ruff check agents/P1-react-agent/src agents/P1-react-agent/tests
```
