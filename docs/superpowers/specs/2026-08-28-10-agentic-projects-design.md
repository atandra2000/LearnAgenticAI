# 10 Agentic AI Projects — Portfolio Design Spec

**Date:** 2026-08-28
**Owner:** Atandra Bharati
**Target outcome:** Full-time Agentic AI Engineer (LangChain / LangGraph / LangSmith stack) at a tech company
**Compute budget:** Ollama Cloud Pro + OpenRouter (multi-model) + ChatGPT Codex Plus
**Frontend depth:** Substantial — Next.js + custom chat UI per project
**Language stack:** Python agent code + TypeScript Next.js shell
**Sequence:** Progressive — each project extends the last and shares infra

---

## 1. Goals & Non-Goals

### Goals
- Cover every interview-grade pattern in the 2026 LangChain job market: ReAct, RAG, multi-agent supervisor, HITL, MCP, deep agents / subagents, structured output, memory, evals, observability, production deploy.
- Each project is a **standalone portfolio piece** (own README, demo, deployed URL or runnable locally), but shares a `common/` infra package so the 10th project ships in days, not weeks.
- Every project ships with a **LangSmith tracing project** + at least one **offline eval dataset** — these are the strongest signals a LangChain hiring manager looks for in a portfolio.
- Every project ships with a **Next.js chat UI** that streams tokens, shows tool calls inline, and links to the LangSmith trace for the run.

### Non-goals
- Building a new framework or competing with LangChain.
- Model fine-tuning (separate track — see existing CoreProjects LLM layer).
- Anything that doesn't exercise the LangChain / LangGraph / LangSmith trio.
- Cramming every API surface — depth on production patterns > breadth across one-off demos.

---

## 2. Job-Market Skill Matrix (the curriculum is the inverse of this)

Pulled from the 2026 job-posting survey (LangChain, Ahura, generic Series-B startups). Each row maps to a project.

| Skill demanded in JDs                                  | Project that teaches it | Why it matters in production                                  |
|--------------------------------------------------------|-------------------------|---------------------------------------------------------------|
| Single-agent ReAct + tool calling                      | **P1**                  | 80% of shipped agents start here                              |
| RAG (chunking, embedding, retrieval, reranking)        | **P2**                  | Most common production pattern                                |
| Conversational memory (short + long term)              | **P3**                  | Every chat product needs this                                 |
| Multi-agent supervisor pattern                         | **P4**                  | Default pattern when one agent hits tool-count or context ceilings |
| Human-in-the-loop interrupts                           | **P5**                  | Highest-leverage safety pattern; required for destructive tools |
| MCP (Model Context Protocol)                           | **P6**                  | 2026 default for tool integration; many JDs list it directly   |
| Deep agents / subagents / planning                     | **P7**                  | The "Claude Code" pattern — long-horizon autonomous work      |
| Structured output + validation                         | **P8**                  | Agents that touch real systems need typed outputs             |
| LangSmith evals + observability + tracing              | **P9**                  | The single most-named "nice to have" in 2026 JDs              |
| Production deploy (auth, rate limit, streaming, monitor) | **P10**                | Without this, the other 9 are demos not products               |

---

## 3. The 10 Projects

### **P1 — ReAct Research Agent** (single-agent foundation)
**One-liner:** A ReAct agent that can search the web, read pages, and answer multi-hop questions with tool calling, traced end-to-end.
**Stack:** LangChain `create_react_agent`, Tavily search, OpenRouter (Claude/GPT-4o-mini), LangSmith tracing, Next.js chat UI.
**Key learnings:** Tool definition, ReAct loop, prompt engineering for tool selection, basic LangSmith traces, token cost debugging.
**Eval dataset:** 30 hand-crafted multi-hop questions with ground-truth URLs.
**Capstone of:** Nothing — this is the base.

### **P2 — Production RAG over Your Own Docs** (retrieval deep-dive)
**One-liner:** RAG over a 200-page PDF (e.g., a long technical manual), with hybrid search, reranking, and a citation-grounded answer.
**Stack:** LangChain document loaders, `RecursiveCharacterTextSplitter` + semantic chunking, OpenAI/Cohere embeddings, Qdrant (local Docker), Cohere rerank, LangSmith context-precision + faithfulness evaluators.
**Key learnings:** Chunking tradeoffs, hybrid search (BM25 + dense), reranking, citation rendering, faithfulness eval.
**Eval dataset:** 50 question/answer pairs from the doc with relevance labels and ideal context chunks.
**Builds on P1:** Agent now has a RAG tool alongside search.

### **P3 — Conversational Agent with Memory** (memory patterns)
**One-liner:** A support-style agent that remembers user preferences across sessions, distinguishes short-term thread memory from long-term profile memory.
**Stack:** LangGraph `StateGraph` with `MemorySaver` (short-term) + Postgres-backed long-term store, semantic search over memory, memory write/read tools.
**Key learnings:** Thread vs cross-thread memory, when to summarize vs store raw, memory poisoning defenses, "delete my data" GDPR pattern.
**Eval dataset:** 20 multi-turn conversations that test recall at session 1 vs session 5.
**Builds on P1, P2:** Adds `messages` and `user_profile` to the state.

### **P4 — Multi-Agent Supervisor (Research Team)** (orchestration)
**One-liner:** A research team of 3 specialist agents (web researcher, code analyst, writer) coordinated by a supervisor agent that routes tasks.
**Stack:** LangGraph supervisor pattern, subgraphs per specialist, `Command` primitive for handoffs, shared `InMemoryStore` for inter-agent notes, LangSmith multi-agent tracing.
**Key learnings:** When supervisor > single-agent, prompt design for routing, subgraph isolation, token cost explosion debugging, hierarchical handoffs.
**Eval dataset:** 15 complex research questions that need all 3 specialists to be answered well.
**Builds on P1–P3:** Each specialist agent is a fully built agent from earlier projects.

### **P5 — Human-in-the-Loop Approval Workflow** (safety)
**One-liner:** An agent that drafts a database-mutating action (e.g., "delete user X"), then **pauses for human approval** before executing — checkpointed and resumable.
**Stack:** LangGraph `interrupt()` + `Command(resume=...)`, Postgres checkpointer, Next.js UI that shows pending interrupts and approve/reject buttons, LangSmith trace of the full pause-resume cycle.
**Key learnings:** `interrupt()` mechanics, checkpointer choice (Memory vs Postgres), state editing, audit log design, confidence-threshold auto-approval.
**Eval dataset:** 10 destructive scenarios (safe + unsafe) to test that unsafe ones always interrupt.
**Builds on P1–P4:** Now a real system, not just an answer machine.

### **P6 — MCP-Powered Tool Server** (protocol integration)
**One-liner:** Build a **custom MCP server** exposing 5 tools (filesystem, sqlite, calendar, gmail, slack), then connect it to a LangGraph agent via `langchain-mcp-adapters`.
**Stack:** `mcp` Python SDK, `langchain-mcp-adapters`, stdio + streamable HTTP transports, OAuth for gmail/slack, Next.js UI showing tool-call tree.
**Key learnings:** MCP protocol mechanics, transport choice (stdio vs streamable HTTP), tool schema design, authentication, combining multiple MCP servers.
**Eval dataset:** 12 cross-tool workflows ("schedule a meeting based on the email thread and post the agenda to Slack").
**Builds on P1–P5:** Agent's tools now come from MCP, not hand-written LangChain tools.

### **P7 — Deep Research Agent (subagents + planning)** (long-horizon autonomy)
**One-liner:** A "deep research" agent that takes a vague topic, plans subtasks, spawns parallel subagents, and synthesizes a long report — Claude Code / Devin-style.
**Stack:** LangChain `deepagents` (or hand-rolled equivalent with LangGraph), `task()` tool for subagent delegation, virtual filesystem for context offload, todo list as planning tool, parallel `Send` API.
**Key learnings:** When to delegate vs do inline, context offloading, parallel fan-out, todo-list discipline, synthesis from subagent reports.
**Eval dataset:** 8 open-ended research topics graded by an LLM-as-judge on coverage, accuracy, structure.
**Builds on P1–P6:** Subagents can themselves use the MCP tools and the RAG stack.

### **P8 — Structured-Output Agent for Real Systems** (typed outputs)
**One-liner:** An agent that fills a typed Pydantic schema (e.g., a customer onboarding form with 12 validated fields) by asking the user questions, validating inputs, and writing to a database.
**Stack:** LangGraph with `with_structured_output` and `Pydantic` v2, retry-with-validation loop, custom validators (regex for phone, libpostal for address), Postgres write, audit trail.
**Key learnings:** Schema design, validation retries, when to use `tool_choice="any"`, partial-fill vs all-or-nothing, error messages that re-prompt the LLM well.
**Eval dataset:** 30 onboarding scenarios with malformed inputs (bad email, missing field, contradictory answers).
**Builds on P1–P7:** Now writes to a real system, not just a chat transcript.

### **P9 — Evaluation & Observability Harness** (the meta-skill)
**One-liner:** A reusable eval harness that runs offline tests against any agent from P1–P8, with LangSmith datasets, LLM-as-judge, and a CI workflow that blocks deploys on regression.
**Stack:** LangSmith `evaluate()`, custom evaluators (exact match, LLM-as-judge, trajectory match), pytest integration, GitHub Actions gate, alert webhooks to Slack.
**Key learnings:** Building eval datasets from prod traces, choosing the right evaluator per task, statistical significance with small N, evaluator prompt engineering, regression detection.
**Eval dataset:** Aggregated gold sets from P1–P8, plus a meta-eval of the evaluators themselves (LLM-judge vs human agreement).
**Builds on all prior projects:** This is the multiplier — every earlier project gets regression-tested through this.

### **P10 — Production Deployment Capstone** (the full stack)
**One-liner:** Pick the strongest P1–P9 project and ship it as a real product: containerized backend, auth, rate limiting, streaming, LangSmith alerts, uptime monitoring, public URL.
**Stack:** FastAPI + uvicorn (or LitServe), Next.js (Vercel), Supabase (Postgres + auth), Stripe for paid tier, LangSmith `online_evaluators` + PagerDuty webhook, GitHub Actions CI/CD, Sentry, basic SOC2-ready logging.
**Key learnings:** Streaming SSE/WebSocket from FastAPI to Next.js, JWT auth, rate-limit middleware, cost guardrails (per-user token caps), graceful degradation when LLM provider is down.
**Eval dataset:** Live production traffic + a load test (`locust`) hitting the public URL.
**Builds on all prior projects:** This is the portfolio hero piece — pick the one with the best demo and ship it.

---

## 4. Architecture — Shared Infrastructure

All 10 projects live in one monorepo with shared infrastructure so each new project is fast to scaffold.

```
LearnAgenticAI/
├── apps/                        # Next.js frontends
│   ├── chat-ui/                 # Reusable chat shell (used by P1-P9)
│   └── P10-public-site/         # Production-grade site for capstone
├── agents/                      # One folder per project
│   ├── P1-react-agent/
│   ├── P2-rag/
│   ├── P3-memory/
│   ├── P4-supervisor/
│   ├── P5-hitl/
│   ├── P6-mcp/
│   ├── P7-deep-research/
│   ├── P8-structured/
│   ├── P9-evals/
│   └── P10-capstone/
├── common/                      # Shared Python package
│   ├── llm.py                   # Model factory (OpenRouter/Ollama routing)
│   ├── tracing.py               # LangSmith setup, project naming
│   ├── evals/                   # Reusable evaluators
│   ├── tools/                   # Common tools (search, file, db)
│   └── ui-bridge/               # SSE/WebSocket helpers
├── docker/                      # docker-compose for postgres, qdrant, redis
├── .github/workflows/           # CI for tests + evals
├── pyproject.toml               # uv workspace
└── README.md
```

**Key shared abstractions:**
- `common.llm.get_model(project: str, task: str) -> BaseChatModel` — routes to the right model per project/task. P1 uses Claude Sonnet for quality, P2's eval uses GPT-4o-mini for cost, P3's local dev uses Ollama Llama-3.
- `common.tracing.setup(project: str) -> None` — wires LangSmith env vars and `tracing_v2_enabled=True`.
- `common.evals.run_suite(agent, dataset_name) -> EvaluationResult` — one function for offline eval that all projects call.
- `apps/chat-ui/` — a Next.js app with a `POST /api/chat` route. The agent backend is just a FastAPI server with an OpenAI-compatible `/v1/chat/completions` endpoint. Drop the same UI in front of any agent.

**Why monorepo, not 10 repos:**
- The chat UI and eval harness are shared — DRY pays back 9x.
- Cross-project changes (e.g., "upgrade LangGraph to 1.2") are one PR.
- You can show interviewers the full breadth by walking one file tree.

---

## 5. Tech Choices

### LLM routing (per project)
- **P1, P4, P7** (highest reasoning load): Claude Sonnet 4.5 via OpenRouter.
- **P2, P5, P8** (tool-heavy, structured output): GPT-4o via OpenRouter.
- **P3, P6** (memory + MCP plumbing): Ollama Cloud Pro (Llama 3.3 70B) — exercises the local-model path.
- **P9** (evals): Mix — judge uses Claude Opus for quality, dataset expansion uses GPT-4o-mini for cost.
- **P10** (capstone): The model that scored best in the P9 eval suite for the chosen task.

### Vector store
- Local: Qdrant (Docker) for P2, P3, P7. Single binary, no managed service needed.
- Hosted (P10 only): Qdrant Cloud or Pinecone.

### Database
- Postgres (Supabase) for checkpointer, long-term memory, structured records. Same instance P5–P10.

### Frontend
- Next.js 15 (App Router) + TypeScript.
- Vercel AI SDK `useChat` hook for streaming.
- Tool-call rendering: a collapsible JSON tree per step.
- LangSmith trace link: a button in the chat header that opens the run's trace.

### Backend
- FastAPI + uvicorn.
- SSE for streaming (avoids WebSocket complexity for one-way token stream).
- Pydantic v2 throughout.

### Orchestration
- LangGraph 1.x.
- `langchain-mcp-adapters` for P6, P7.
- `deepagents` for P7 (or hand-rolled if the library is unstable — verify at build time).

### Observability
- LangSmith for traces + evals + datasets (one project per agent, named `P1-react-agent`, `P2-rag`, etc.).
- Sentry for backend error tracking.
- PagerDuty webhook (P10 only) for production alerts.

---

## 6. Execution Plan

### Phase 0 — Infra (3-4 days, do once)
- Set up monorepo, `pyproject.toml` with `uv`, Docker compose for Postgres + Qdrant.
- Build `common/` package (LLM factory, tracing setup, eval runner).
- Build `apps/chat-ui/` Next.js shell (streaming chat, tool-call rendering, trace link).
- Set up LangSmith workspace with 10 named projects.
- One smoke-test agent (P0) that just echoes — proves the wiring.

### Phase 1 — Foundations (P1 → P2 → P3) (~5-6 weeks)
- P1: ReAct agent, end-to-end. Tests, eval dataset, demo.
- P2: Add RAG, swap out search tool. New eval dataset, faithfulness eval.
- P3: Add memory. Multi-turn eval, memory isolation tests.

### Phase 2 — Orchestration (P4 → P5 → P6) (~5-6 weeks)
- P4: Supervisor + 3 subagents. Multi-agent tracing.
- P5: Add HITL interrupts. Postgres checkpointer. Audit log.
- P6: Build custom MCP server + adapter. Cross-tool evals.

### Phase 3 — Autonomy + Real Systems (P7 → P8) (~3-4 weeks)
- P7: Deep research agent with subagents + planning.
- P8: Structured output with validation retries. DB writes.

### Phase 4 — Meta + Ship (P9 → P10) (~3-4 weeks)
- P9: Eval harness, CI gate, regression tests on all 9 prior projects.
- P10: Pick the strongest project, deploy, monitor, public URL.

**Total: ~16-20 weeks of part-time work, or ~8-10 weeks full-time.**

### Suggested order rationale
- Foundations before orchestration (you can't supervise what you can't build).
- HITL before MCP (HITL is conceptually simpler and tests your understanding of state).
- Deep agents after supervisor (deep agents = supervisor + planning + context offload — you need the base pattern first).
- Evals second-to-last (P9 needs all 8 prior projects to have datasets).
- Capstone last (you need a winning candidate to pick from P1–P9).

---

## 7. Per-Project Acceptance Criteria

Every project (P1–P10) must ship with:

1. **README.md** — what it does, architecture diagram, how to run, eval results.
2. **Working Next.js demo** — `cd apps/chat-ui && pnpm dev` reaches a runnable UI.
3. **Offline eval suite** — `make eval` runs against a LangSmith dataset and prints scores.
4. **LangSmith trace** — the README has a screenshot or public link to a real trace.
5. **At least 3 tests** — unit (a function), integration (an agent run), eval (a regression check).
6. **Cost report** — README has a table of cost-per-100-runs for each model used. This is a hiring signal — interviewers love engineers who think about unit economics.

P10 additionally requires: deployed URL, auth, rate limit, monitoring, alert.

---

## 8. Risk & Mitigation

| Risk                                                       | Likelihood | Mitigation                                                                                          |
|------------------------------------------------------------|------------|-----------------------------------------------------------------------------------------------------|
| LangChain / LangGraph API churn                             | High       | Pin versions in `pyproject.toml`; abstract behind `common.llm` so a breaking change is one PR       |
| OpenRouter outage                                          | Medium     | `common.llm` supports fallback to Ollama Cloud Pro; tested in P10                                   |
| Eval datasets get stale                                    | Medium     | P9 has a "refresh dataset from prod traces" script; run monthly                                     |
| LLM judge disagrees with human (evals not trustworthy)     | High       | P9 includes a meta-eval: human labels 50 runs, report judge-human agreement, calibrate threshold   |
| Scope creep on chat UI                                     | High       | UI is in `apps/chat-ui/`; once a feature works for P1, lock it. P10 may add polish, not earlier      |
| LangSmith cost surprise                                    | Medium     | Use `LANGSMITH_TRACING=true` selectively in CI; sample 10% of prod traffic                          |
| API budget burn                                            | Medium     | Set per-project token cap in `common/llm.py`; dashboard in LangSmith shows daily spend              |
| Deepagents library instability                             | Medium     | Verify against latest release at P7 kickoff; fall back to hand-rolled LangGraph if needed           |

---

## 9. Success Metrics

The portfolio is "done" when:

- **Coverage:** All 10 rows of the §2 skill matrix have a project that demonstrates them with non-trivial depth (not a one-line tool call).
- **Eval maturity:** Every project has an offline eval that runs in CI and a published score. P9 has a meta-eval proving the evaluators are reliable.
- **Demo polish:** Each project's `apps/chat-ui/` demo is sub-2-second time-to-first-token and renders tool calls cleanly.
- **Production ready:** P10 is deployed with auth, monitoring, and a public URL.
- **Interview ready:** You can whiteboard the architecture of any project in 5 minutes and have a LangSmith trace ready to share.
- **Story:** The README's of all 10 projects together tell a coherent narrative of progression from toy to production.

---

## 10. Out of Scope (deliberate)

- Model fine-tuning — already covered by your existing `LLM/` layer.
- Computer-use agents, browser-use agents, GUI automation — different niche, not core to the LangChain job market.
- Voice agents — different stack (Pipecat, LiveKit), separate portfolio.
- A custom agent framework — not what the market is hiring for.
- More than 10 projects — diminishing returns; better to ship 10 strong than 15 weak.

---

## 11. Open Questions (resolve before P3)

1. **P2 doc choice:** Long technical PDF — your pick. A great option is the LangGraph docs themselves (meta but instructive).
2. **P6 MCP server domain:** The 5 tools (filesystem, sqlite, calendar, gmail, slack) are illustrative — could be different. Real gmail/slack need OAuth, which adds 2-3 days. Alternative: pure-local stack (filesystem + sqlite + a custom internal-API + weather API + arxiv).
3. **P10 pick:** After P1–P9, pick the best. Hypothesis: P4 (multi-agent research team) or P7 (deep research) makes the strongest demo.

---

## 12. References

- [LangGraph Production Multi-Agent Systems Patterns & Best Practices](https://www.bloorgroup.com/article/langgraph-production-multi-agent-systems-patterns-best-practices/)
- [LangSmith Evaluation Platform](https://www.langchain.com/langsmith/evaluation?gad_campaignid=23342761677)
- [LangSmith Observability Platform](https://www.langchain.com/langsmith/observability)
- [LangSmith Observability LLM Tutorial (Customer Support Chatbot with RAG)](https://docs.langchain.com/langsmith/observability-llm-tutorial)
- [LangSmith in Production: Observability, Evaluation, and Debugging AI Agents](https://www.abhishekchauhan.it/blog/langsmith-production-observability-evaluation-debugging)
- [langchain-mcp-adapters on GitHub](https://github.com/langchain-ai/langchain-mcp-adapters)
- [MCP for LangGraph Developers: From Basics to Production](https://pub.towardsai.net/mcp-for-langgraph-developers-from-basics-to-production)
- Job-post scan (internal): LangChain Research Engineer, LangChain Fullstack Applied AI, LangChain Deployed Engineer, Ahura Agentic AI Engineer — 2026-08.
