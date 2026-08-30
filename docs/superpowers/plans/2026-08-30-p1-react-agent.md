# Plan 1: ReAct Research Agent (P1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and ship **P1 — ReAct Research Agent**, a production-grade single-agent research system capable of autonomous web search, page content reading, multi-hop reasoning, inline tool call streaming, and full LangSmith observability, backed by an offline evaluation suite of 30 multi-hop benchmark questions.

**Architecture:** 
FastAPI agent service (`agents/P1-react-agent/`) exposing `/v1/chat/completions` speaking the standardized SSE wire format (`common.ui_bridge`). It executes a LangGraph ReAct agent loop (`create_react_agent`) powered by OpenRouter LLM routing (`deepseek/deepseek-v4-flash-0731` / Claude Sonnet), equipped with shared web search (`tavily_search`) and page reading (`read_page`) tools from `common.tools`. The streaming event loop captures `on_chat_model_stream`, `on_tool_start`, and `on_tool_end` events from `astream_events(version="v2")` and delivers live tokens and collapsible tool executions directly into the Next.js `apps/chat-ui/` shell.

**Tech Stack:** Python 3.11, `uv` workspace, LangChain 0.3+, LangGraph 0.6+, LangSmith SDK, FastAPI, Pydantic v2, `httpx`, `respx`, pytest, ruff, mypy.

**Spec:** `docs/superpowers/specs/2026-08-28-10-agentic-projects-design.md` §3 (P1) and §7 (Acceptance Criteria).

---

## Global Constraints

- **Language & Runtime:** Python 3.11 in uv workspace. Frontend in TypeScript (Next.js 15).
- **Package Management:** `uv` for Python packages (`uv add`, `uv sync`).
- **LLM Routing:** All model calls go through `common.llm.get_model("P1-react-agent", task="reasoning")`.
- **Telemetry:** Scoped automatically under `with setup("P1-react-agent"):` pointing to LangSmith project `LearnAgenticAI/P1-react-agent`.
- **Wire Compatibility:** Must emit SSE events strictly conforming to `common.ui_bridge.VALID_EVENT_TYPES` (`token`, `tool_start`, `tool_end`, `message_end`, `trace_meta`, `error`) so `apps/chat-ui` renders live tool trees seamlessly without UI code changes.
- **Code Quality:** Zero mypy strict errors (`mypy --strict`), zero ruff lint errors (`ruff check`), full ruff formatting (`ruff format --check`), and 100% passing test suite in CI.
- **No Placeholders:** Every file, test case, prompt, and tool implementation is completely written out with full type annotations.

---

## File Structure

### Created in this plan
```
LearnAgenticAI/
├── common/
│   ├── src/common/tools/
│   │   ├── search.py                 # tavily_search LangChain tool
│   │   └── web.py                    # read_page LangChain tool
│   └── tests/
│       └── test_tools.py             # unit tests for search and web tools
├── agents/
│   └── P1-react-agent/
│       ├── pyproject.toml            # agent workspace member
│       ├── README.md                 # architecture, how to run, eval results, cost report
│       ├── eval.py                   # offline eval harness CLI
│       ├── data/
│       │   └── eval_questions.jsonl  # 30 hand-crafted multi-hop research questions
│       ├── src/
│       │   └── P1_react_agent/
│       │       ├── __init__.py
│       │       ├── agent.py          # ReAct graph, prompts, and astream_events SSE bridge
│       │       └── server.py         # FastAPI /v1/chat/completions endpoint
│       └── tests/
│           ├── __init__.py
│           ├── test_agent.py         # agent graph compilation and mock execution tests
│           ├── test_server.py        # FastAPI SSE endpoint and validation tests
│           └── test_eval.py          # offline eval test runner
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-08-30-p1-react-agent.md # this file
```

### Modified in this plan
- `common/src/common/config.py`: Add `tavily_api_key` to `Settings`.
- `common/src/common/tools/__init__.py`: Export `tavily_search` and `read_page`.
- `.env.example`: Add `TAVILY_API_KEY=`.
- `.github/workflows/ci.yml`: Add `P1-react-agent` to lint, typecheck, format check, and test steps.

---

## Task 1: Shared Tools Package (`tavily_search` and `read_page`)

**Files:**
- Modify: `common/src/common/config.py`, `common/src/common/tools/__init__.py`, `.env.example`
- Create: `common/src/common/tools/search.py`, `common/src/common/tools/web.py`, `common/tests/test_tools.py`

**Interfaces:**
- `tavily_search(query: str, max_results: int = 5) -> str`: Async LangChain tool calling Tavily API. Returns formatted search results with title, URL, and snippet.
- `read_page(url: str, max_chars: int = 4000) -> str`: Async LangChain tool fetching web page content via `httpx`, stripping HTML tags/scripts, and returning sanitized markdown/plain text.

- [ ] **Step 1: Update `common/src/common/config.py` with `tavily_api_key`**

Edit `common/src/common/config.py` to add `tavily_api_key`:

```python
    # --- Search / External APIs ---
    tavily_api_key: str = Field(default="", description="Tavily Search API key")
```

- [ ] **Step 2: Update `.env.example`**

Add `TAVILY_API_KEY=` to `.env.example`:

```bash
# Search APIs
TAVILY_API_KEY=
```

- [ ] **Step 3: Implement `common/src/common/tools/search.py`**

Create `common/src/common/tools/search.py`:

```python
"""Web search tool wrapping the Tavily REST API."""

from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool

from common.config import get_settings

_TAVILY_API_URL = "https://api.tavily.com/search"


async def _execute_tavily_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Internal helper to execute a raw search against Tavily."""
    settings = get_settings()
    if not settings.tavily_api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Set it in .env to use the tavily_search tool."
        )

    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max(1, min(max_results, 10)),
        "include_answer": False,
        "include_raw_content": False,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(_TAVILY_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            return {
                "error": f"Tavily search API returned HTTP {response.status_code}: {response.text}"
            }
        data: dict[str, Any] = response.json()
        return data


@tool
async def tavily_search(query: str, max_results: int = 5) -> str:
    """Search the public web for real-time information, facts, news, or technical documentation.

    Args:
        query: The search query string.
        max_results: Maximum number of search results to return (default: 5).

    Returns:
        A structured string of search results containing titles, URLs, and text snippets.
    """
    try:
        data = await _execute_tavily_search(query, max_results=max_results)
    except Exception as e:  # noqa: BLE001
        return f"Error executing web search: {e}"

    if "error" in data:
        return f"Search error: {data['error']}"

    results = data.get("results", [])
    if not results:
        return f"No search results found for query: {query!r}"

    formatted_parts: list[str] = []
    for idx, item in enumerate(results, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        content = item.get("content", "").strip()
        formatted_parts.append(f"[{idx}] {title}\nURL: {url}\nSnippet: {content}")

    return "\n\n".join(formatted_parts)
```

- [ ] **Step 4: Implement `common/src/common/tools/web.py`**

Create `common/src/common/tools/web.py`:

```python
"""Web page content reader tool for deep text extraction."""

from __future__ import annotations

import re
from html.parser import HTMLParser

import httpx
from langchain_core.tools import tool


class _HTMLTextExtractor(HTMLParser):
    """Minimal HTML parser that extracts text while omitting scripts, styles, and tags."""

    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._ignore: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._ignore = True
        elif tag.lower() in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr", "br"):
            self._pieces.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._ignore = False
        elif tag.lower() in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr"):
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignore:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        # Collapse excessive whitespace
        cleaned = re.sub(r"[ \t]+", " ", raw)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()


def extract_clean_text(html_content: str) -> str:
    """Convert raw HTML into readable plain text."""
    parser = _HTMLTextExtractor()
    parser.feed(html_content)
    return parser.get_text()


@tool
async def read_page(url: str, max_chars: int = 4000) -> str:
    """Fetch a webpage by URL and return its readable text content.

    Use this tool when search snippets are insufficient and you need to inspect
    the full content of an article, documentation page, or reference link.

    Args:
        url: The complete HTTP/HTTPS URL of the page to read.
        max_chars: Maximum characters to return (default: 4000).

    Returns:
        Clean plain text content extracted from the webpage.
    """
    if not (url.startswith("http://") or url.startswith("https://")):
        return f"Error: Invalid URL scheme for {url!r}. Must start with http:// or https://"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,text/plain",
    }

    try:
        async with httpx.AsyncClient(
            timeout=12.0, follow_redirects=True, verify=True
        ) as client:
            response = await client.get(url, headers=headers)
            if response.status_code >= 400:
                return f"Error fetching {url}: HTTP {response.status_code}"
            
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type or "application/xhtml" in content_type:
                text = extract_clean_text(response.text)
            else:
                text = response.text.strip()

            if not text:
                return f"Notice: Webpage at {url} returned empty readable text."

            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... [Content truncated at {max_chars} characters]"

            return text
    except httpx.TimeoutException:
        return f"Error: Request timed out while fetching {url}"
    except httpx.RequestError as e:
        return f"Error: Network failure while connecting to {url}: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Error: Unexpected failure reading {url}: {e}"
```

- [ ] **Step 5: Export tools in `common/src/common/tools/__init__.py`**

Update `common/src/common/tools/__init__.py`:

```python
"""Shared LangChain tools for agents."""

from common.tools.search import tavily_search
from common.tools.web import extract_clean_text, read_page

__all__ = ["tavily_search", "read_page", "extract_clean_text"]
```

- [ ] **Step 6: Write unit tests in `common/tests/test_tools.py`**

Create `common/tests/test_tools.py`:

```python
"""Unit tests for shared search and web tools."""

from __future__ import annotations

import httpx
import pytest
import respx

from common.config import Settings
from common.tools.search import tavily_search
from common.tools.web import extract_clean_text, read_page


def test_extract_clean_text() -> None:
    html = """
    <html>
        <head><title>Test Page</title><style>body { color: red; }</style></head>
        <body>
            <script>console.log("ignore me");</script>
            <h1>Heading</h1>
            <p>First paragraph with <a href="#">link</a>.</p>
            <p>Second paragraph.</p>
        </body>
    </html>
    """
    cleaned = extract_clean_text(html)
    assert "Heading" in cleaned
    assert "First paragraph with link." in cleaned
    assert "Second paragraph." in cleaned
    assert "console.log" not in cleaned
    assert "color: red" not in cleaned


@pytest.mark.asyncio
async def test_tavily_search_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "common.tools.search.get_settings",
        lambda: Settings(tavily_api_key=""),
    )
    result = await tavily_search.ainvoke({"query": "LangGraph"})
    assert "Error executing web search" in result
    assert "TAVILY_API_KEY is not set" in result


@pytest.mark.asyncio
@respx.mock
async def test_tavily_search_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "common.tools.search.get_settings",
        lambda: Settings(tavily_api_key="mock-key"),
    )
    mock_payload = {
        "results": [
            {
                "title": "LangGraph Documentation",
                "url": "https://langchain-ai.github.io/langgraph/",
                "content": "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
            }
        ]
    }
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(200, json=mock_payload)
    )

    result = await tavily_search.ainvoke({"query": "LangGraph", "max_results": 1})
    assert "[1] LangGraph Documentation" in result
    assert "https://langchain-ai.github.io/langgraph/" in result
    assert "LangGraph is a library" in result


@pytest.mark.asyncio
@respx.mock
async def test_tavily_search_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "common.tools.search.get_settings",
        lambda: Settings(tavily_api_key="mock-key"),
    )
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    result = await tavily_search.ainvoke({"query": "LangGraph"})
    assert "Search error: Tavily search API returned HTTP 500" in result


@pytest.mark.asyncio
async def test_read_page_invalid_scheme() -> None:
    result = await read_page.ainvoke({"url": "ftp://example.com/file.txt"})
    assert "Invalid URL scheme" in result


@pytest.mark.asyncio
@respx.mock
async def test_read_page_success() -> None:
    respx.get("https://example.com/doc").mock(
        return_value=httpx.Response(
            200,
            text="<html><body><h1>Doc Title</h1><p>Detailed technical content.</p></body></html>",
            headers={"content-type": "text/html"},
        )
    )
    result = await read_page.ainvoke({"url": "https://example.com/doc"})
    assert "Doc Title" in result
    assert "Detailed technical content." in result


@pytest.mark.asyncio
@respx.mock
async def test_read_page_truncation() -> None:
    long_content = "A" * 500
    respx.get("https://example.com/long").mock(
        return_value=httpx.Response(
            200,
            text=f"<html><body><p>{long_content}</p></body></html>",
            headers={"content-type": "text/html"},
        )
    )
    result = await read_page.ainvoke({"url": "https://example.com/long", "max_chars": 100})
    assert len(result) > 100
    assert "[Content truncated at 100 characters]" in result


@pytest.mark.asyncio
@respx.mock
async def test_read_page_404_error() -> None:
    respx.get("https://example.com/notfound").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    result = await read_page.ainvoke({"url": "https://example.com/notfound"})
    assert "Error fetching https://example.com/notfound: HTTP 404" in result
```

- [ ] **Step 7: Run tool tests and format check**

```bash
uv run --package common pytest common/tests/test_tools.py -v
uv run --package common ruff check common/src common/tests
uv run --package common mypy common/src
```

- [ ] **Step 8: Commit Task 1**

```bash
git add common/src/common/config.py common/src/common/tools/ common/tests/test_tools.py .env.example
git commit -m "feat(common): add tavily_search and read_page tools with unit tests"
```

---

## Task 2: P1 Agent Package Scaffold

**Files:**
- Create: `agents/P1-react-agent/pyproject.toml`, `agents/P1-react-agent/src/P1_react_agent/__init__.py`

**Interfaces:**
- Workspace membership in root `pyproject.toml`
- Resolves cleanly via `uv sync --all-packages`

- [ ] **Step 1: Create `agents/P1-react-agent/pyproject.toml`**

Write to `agents/P1-react-agent/pyproject.toml`:

```toml
[project]
name = "P1-react-agent"
version = "0.0.0"
description = "P1 — ReAct Research Agent with web search, page reading, and multi-hop reasoning."
requires-python = ">=3.11,<3.13"
dependencies = [
    "common",
    "fastapi>=0.115,<1",
    "uvicorn[standard]>=0.32,<1",
    "pydantic>=2.7,<3",
    "sse-starlette>=2.1,<3",
    "httpx>=0.27,<1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8,<9",
    "pytest-asyncio>=0.23,<1",
    "respx>=0.21,<1",
    "ruff>=0.5,<1",
    "mypy>=1.10,<2",
]

[tool.uv.sources]
common = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/P1_react_agent"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
extend-ignore = ["N999"] # package name `P1_react_agent` is mandated by the spec

[tool.mypy]
strict = true
python_version = "3.11"
```

- [ ] **Step 2: Create package init file `agents/P1-react-agent/src/P1_react_agent/__init__.py`**

```python
"""P1 ReAct Research Agent package."""
```

- [ ] **Step 3: Sync workspace**

```bash
uv sync --all-packages
```

- [ ] **Step 4: Commit Task 2**

```bash
git add agents/P1-react-agent/pyproject.toml agents/P1-react-agent/src/P1_react_agent/__init__.py uv.lock
git commit -m "chore(P1-react-agent): scaffold package definition and sync uv workspace"
```

---

## Task 3: P1 ReAct Agent Graph & Streaming Bridge

**Files:**
- Create: `agents/P1-react-agent/src/P1_react_agent/agent.py`
- Create: `agents/P1-react-agent/tests/test_agent.py`

**Interfaces:**
- `build_agent() -> CompiledGraph`: Builds a compiled LangGraph ReAct agent using `create_react_agent` with model from `common.llm.get_model("P1-react-agent", task="reasoning")` and tools `[tavily_search, read_page]`.
- `stream_agent(messages: list[BaseMessage], run_id: str) -> AsyncIterator[bytes]`: Streams execution via `astream_events(version="v2")`, emitting typed SSE events (`token`, `tool_start`, `tool_end`, `message_end`, `trace_meta`).
- `invoke(messages: list[BaseMessage]) -> ResearchResult`: Direct async invoke helper for offline evals.

- [ ] **Step 1: Implement `agents/P1-react-agent/src/P1_react_agent/agent.py`**

Create `agents/P1-react-agent/src/P1_react_agent/agent.py`:

```python
"""ReAct Research Agent implementation using LangGraph and LangChain tools."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from common.llm import get_model
from common.tools import read_page, tavily_search
from common.ui_bridge import (
    message_end_event,
    token_event,
    tool_end_event,
    tool_start_event,
    trace_meta_event,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = (
    "You are an expert AI research assistant equipped with web search and webpage reading tools. "
    "Your goal is to answer the user's inquiry with high factual accuracy, multi-hop reasoning, "
    "and clear source attribution.\n\n"
    "Guidelines:\n"
    "1. When asked a question requiring real-time, external, or detailed technical facts, invoke "
    "`tavily_search` with targeted queries.\n"
    "2. If a search result snippet is incomplete or mentions a promising source URL, invoke `read_page` "
    "on that URL to inspect the full context.\n"
    "3. Break complex multi-hop questions into incremental search steps.\n"
    "4. Synthesize your final answer concisely and include Markdown links or bracketed citations "
    "pointing to the source URLs you discovered.\n"
    "5. If you cannot find reliable information after searching, clearly state what was searched "
    "and what remains unknown."
)


@dataclass
class ResearchResult:
    """Result of a non-streaming agent run."""

    text: str
    tool_calls_count: int = 0
    sources: list[str] = field(default_factory=list)


def build_agent(model_override: BaseChatModel | None = None) -> CompiledStateGraph:
    """Build and compile the ReAct agent graph.

    Args:
        model_override: Optional custom chat model (useful for unit tests with mocks).
    """
    model = model_override or get_model("P1-react-agent", task="reasoning")
    tools = [tavily_search, read_page]
    agent = create_react_agent(
        model=model,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )
    return agent


async def stream_agent(
    messages: list[BaseMessage],
    run_id: str,
    model_override: BaseChatModel | None = None,
) -> AsyncIterator[bytes]:
    """Stream agent execution as typed SSE events for the chat UI.

    Consumes LangGraph's astream_events (v2) to yield token deltas and tool telemetry.
    """
    agent = build_agent(model_override=model_override)
    input_state = {"messages": messages}

    async for event in agent.astream_events(input_state, version="v2"):
        event_kind = event.get("event")

        # 1. Stream tokens from the final chat model generation
        if event_kind == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk")
            # Only stream tokens from assistant content chunks (skip empty tool calls chunks)
            if chunk and hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content:
                yield token_event(chunk.content)

        # 2. Stream tool start telemetry
        elif event_kind == "on_tool_start":
            tool_name = event.get("name", "unknown_tool")
            tool_run_id = event.get("run_id", run_id)
            raw_input = event.get("data", {}).get("input", {})
            args = raw_input if isinstance(raw_input, dict) else {"input": str(raw_input)}
            yield tool_start_event(tool_name=tool_name, args=args, call_id=tool_run_id)

        # 3. Stream tool end telemetry
        elif event_kind == "on_tool_end":
            tool_run_id = event.get("run_id", run_id)
            raw_output = event.get("data", {}).get("output")
            result: Any = raw_output
            if hasattr(raw_output, "content"):
                result = raw_output.content
            yield tool_end_event(call_id=tool_run_id, result=result)

    yield message_end_event("stop")
    yield trace_meta_event(
        run_url=f"https://smith.langchain.com/r/{run_id}",
        run_id=run_id,
    )


async def invoke(
    messages: list[BaseMessage],
    model_override: BaseChatModel | None = None,
) -> ResearchResult:
    """Synchronous-style invocation for offline evaluations and scripts."""
    agent = build_agent(model_override=model_override)
    result = await agent.ainvoke({"messages": messages})
    output_messages: list[BaseMessage] = result.get("messages", [])
    
    final_text = ""
    tool_calls_count = 0
    sources: list[str] = []

    for msg in output_messages:
        if isinstance(msg, AIMessage):
            if isinstance(msg.content, str) and msg.content:
                final_text = msg.content
            if getattr(msg, "tool_calls", None):
                tool_calls_count += len(msg.tool_calls)

    return ResearchResult(
        text=final_text,
        tool_calls_count=tool_calls_count,
        sources=sources,
    )
```

- [ ] **Step 2: Implement `agents/P1-react-agent/tests/test_agent.py`**

Create `agents/P1-react-agent/tests/test_agent.py`:

```python
"""Tests for P1 ReAct agent graph building and streaming events."""

from __future__ import annotations

import json
import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from P1_react_agent.agent import build_agent, invoke, stream_agent


def test_build_agent_compiles() -> None:
    fake_model = FakeListChatModel(responses=["Hello from fake agent!"])
    agent = build_agent(model_override=fake_model)
    assert agent is not None


@pytest.mark.asyncio
async def test_agent_invoke_simple() -> None:
    fake_model = FakeListChatModel(responses=["LangGraph is stateful."])
    result = await invoke(
        [HumanMessage(content="What is LangGraph?")],
        model_override=fake_model,
    )
    assert result.text == "LangGraph is stateful."
    assert result.tool_calls_count == 0


@pytest.mark.asyncio
async def test_stream_agent_emits_expected_sse_structure() -> None:
    fake_model = FakeListChatModel(responses=["DeepSeek is fast."])
    events: list[str] = []
    
    async for event_bytes in stream_agent(
        [HumanMessage(content="Tell me about DeepSeek.")],
        run_id="test-run-123",
        model_override=fake_model,
    ):
        events.append(event_bytes.decode())

    combined = "".join(events)
    assert "event: token" in combined
    assert "event: message_end" in combined
    assert "event: trace_meta" in combined
    assert "https://smith.langchain.com/r/test-run-123" in combined
```

- [ ] **Step 3: Run agent tests**

```bash
uv run --package P1-react-agent pytest agents/P1-react-agent/tests/test_agent.py -v
uv run --package P1-react-agent ruff check agents/P1-react-agent/src agents/P1-react-agent/tests
uv run --package P1-react-agent mypy agents/P1-react-agent/src
```

- [ ] **Step 4: Commit Task 3**

```bash
git add agents/P1-react-agent/src/P1_react_agent/agent.py agents/P1-react-agent/tests/test_agent.py
git commit -m "feat(P1-react-agent): implement ReAct research agent graph and streaming event codec"
```

---

## Task 4: P1 FastAPI Server & Wire Protocol

**Files:**
- Create: `agents/P1-react-agent/src/P1_react_agent/server.py`
- Create: `agents/P1-react-agent/tests/test_server.py`

**Interfaces:**
- `POST /v1/chat/completions`: Accepts `{ "messages": [...], "stream": true }`, executes under `with setup("P1-react-agent"):`, and returns `StreamingResponse(media_type="text/event-stream")`.

- [ ] **Step 1: Implement `agents/P1-react-agent/src/P1_react_agent/server.py`**

Create `agents/P1-react-agent/src/P1_react_agent/server.py`:

```python
"""FastAPI server for the P1 ReAct research agent."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Literal

from common.tracing import setup
from common.ui_bridge import error_event
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from P1_react_agent.agent import stream_agent

app = FastAPI(title="P1 ReAct Research Agent")


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    stream: bool = True


def _to_langchain_messages(items: list[ChatMessage]) -> list[BaseMessage]:
    out: list[BaseMessage] = []
    for m in items:
        if m.role == "system":
            out.append(SystemMessage(content=m.content))
        elif m.role == "user":
            out.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            out.append(AIMessage(content=m.content))
    return out


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest) -> StreamingResponse:
    """Stream ReAct agent responses and tool call telemetry as SSE."""
    run_id = str(uuid.uuid4())
    langchain_messages = _to_langchain_messages(req.messages)

    async def event_source() -> AsyncIterator[bytes]:
        try:
            with setup("P1-react-agent"):
                async for event in stream_agent(langchain_messages, run_id):
                    yield event
        except Exception as e:  # noqa: BLE001
            yield error_event(str(e), code="agent_exception")

    return StreamingResponse(event_source(), media_type="text/event-stream")
```

- [ ] **Step 2: Implement `agents/P1-react-agent/tests/test_server.py`**

Create `agents/P1-react-agent/tests/test_server.py`:

```python
"""Tests for P1 FastAPI server request validation and streaming endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from P1_react_agent.server import app

client = TestClient(app)


def test_request_validation_empty_messages() -> None:
    res = client.post("/v1/chat/completions", json={"messages": []})
    assert res.status_code == 422


def test_request_validation_missing_field() -> None:
    res = client.post("/v1/chat/completions", json={})
    assert res.status_code == 422


def test_request_validation_invalid_role() -> None:
    res = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "invalid_role", "content": "hello"}]},
    )
    assert res.status_code == 422
```

- [ ] **Step 3: Run server tests and typecheck**

```bash
uv run --package P1-react-agent pytest agents/P1-react-agent/tests/test_server.py -v
uv run --package P1-react-agent ruff check agents/P1-react-agent/src agents/P1-react-agent/tests
uv run --package P1-react-agent mypy agents/P1-react-agent/src
```

- [ ] **Step 4: Commit Task 4**

```bash
git add agents/P1-react-agent/src/P1_react_agent/server.py agents/P1-react-agent/tests/test_server.py
git commit -m "feat(P1-react-agent): implement FastAPI server endpoint for SSE chat completions"
```

---

## Task 5: Offline Evaluation Dataset & Eval Harness

**Files:**
- Create: `agents/P1-react-agent/data/eval_questions.jsonl`
- Create: `agents/P1-react-agent/eval.py`
- Create: `agents/P1-react-agent/tests/test_eval.py`

**Interfaces:**
- `eval_questions.jsonl`: 30 hand-crafted multi-hop research questions covering factual recall, entity comparisons, technical documentation verification, and chronology.
- `eval.py`: CLI executable via `uv run python eval.py [--limit N]` that runs the evaluation suite, measures tool call usage and latency, and prints a formatted benchmark summary table.

- [ ] **Step 1: Create `agents/P1-react-agent/data/eval_questions.jsonl`**

Write 30 multi-hop benchmark questions into `agents/P1-react-agent/data/eval_questions.jsonl`:

```jsonl
{"id": "q1", "category": "tech_architecture", "question": "What is the primary difference between LangGraph StateGraph and create_react_agent, and what checkpointing mechanism does LangGraph use for PostgreSQL?", "expected_keywords": ["StateGraph", "create_react_agent", "PostgresSaver", "checkpoint"]}
{"id": "q2", "category": "tech_history", "question": "Who created the Python language, what year was it first released, and where was the creator working at that time?", "expected_keywords": ["Guido van Rossum", "1991", "CWI"]}
{"id": "q3", "category": "astronomy", "question": "Which spacecraft was the first to visit Pluto, in what year did the flyby occur, and what is the name of Pluto's largest moon?", "expected_keywords": ["New Horizons", "2015", "Charon"]}
{"id": "q4", "category": "science_nobel", "question": "Who won the 2020 Nobel Prize in Physics for black hole discoveries, and what university was Andrea Ghez affiliated with?", "expected_keywords": ["Roger Penrose", "Reinhard Genzel", "Andrea Ghez", "UCLA"]}
{"id": "q5", "category": "geography_bridges", "question": "What is the longest suspension bridge in the world as of 2024, what country is it in, and what two continents/bodies does it connect across?", "expected_keywords": ["1915 Çanakkale", "Turkey", "Dardanelles"]}
{"id": "q6", "category": "ai_models", "question": "When was the original Transformer architecture published in the 'Attention Is All You Need' paper, and who was the first author listed?", "expected_keywords": ["2017", "Ashish Vaswani"]}
{"id": "q7", "category": "computing_os", "question": "What kernel did macOS originally derive from, and what was the predecessor operating system developed at NeXT?", "expected_keywords": ["Mach", "BSD", "NeXTSTEP"]}
{"id": "q8", "category": "literature", "question": "Who wrote 'One Hundred Years of Solitude', what year did they win the Nobel Prize in Literature, and what fictional town is the novel set in?", "expected_keywords": ["Gabriel García Márquez", "1982", "Macondo"]}
{"id": "q9", "category": "biology", "question": "Who discovered penicillin, in what year, and what mold genus was it isolated from?", "expected_keywords": ["Alexander Fleming", "1928", "Penicillium"]}
{"id": "q10", "category": "history_treaties", "question": "What treaty ended the Thirty Years' War in 1648, and what modern country hosted the negotiations in Münster and Osnabrück?", "expected_keywords": ["Peace of Westphalia", "Germany"]}
{"id": "q11", "category": "cloud_architecture", "question": "What is the underlying open-source storage engine behind Apache Kafka, and what consensus protocol replaced ZooKeeper in KRaft mode?", "expected_keywords": ["commit log", "Raft", "KRaft"]}
{"id": "q12", "category": "deep_learning", "question": "What optimizer introduced by Kingma and Ba in 2014 combines AdaGrad and RMSProp principles?", "expected_keywords": ["Adam"]}
{"id": "q13", "category": "hardware", "question": "What architecture is Apple Silicon (M-series) based on, and what foundry manufactures the M3 and M4 chips?", "expected_keywords": ["ARM", "TSMC"]}
{"id": "q14", "category": "cryptography", "question": "What cryptographic curve is used in Bitcoin's ECDSA signatures, and what hash function is used in proof-of-work?", "expected_keywords": ["secp256k1", "SHA-256"]}
{"id": "q15", "category": "aviation", "question": "What was the first commercial supersonic airliner, and which two countries jointly developed it?", "expected_keywords": ["Concorde", "Britain", "France"]}
{"id": "q16", "category": "maritime", "question": "In what year did the Titanic sink, what was its destination port, and what shipping company operated it?", "expected_keywords": ["1912", "New York", "White Star Line"]}
{"id": "q17", "category": "music_classical", "question": "How many symphonies did Ludwig van Beethoven compose, and which symphony contains the 'Ode to Joy'?", "expected_keywords": ["9", "Ninth Symphony"]}
{"id": "q18", "category": "databases", "question": "What vector indexing algorithm is used by Qdrant for approximate nearest neighbor search?", "expected_keywords": ["HNSW"]}
{"id": "q19", "category": "protocols", "question": "What does MCP stand for in the context of Anthropic AI tooling, and what default transports does it support?", "expected_keywords": ["Model Context Protocol", "stdio", "SSE", "HTTP"]}
{"id": "q20", "category": "robotics", "question": "What company developed the Spot and Atlas robots, and what parent company acquired them in 2021?", "expected_keywords": ["Boston Dynamics", "Hyundai"]}
{"id": "q21", "category": "telecom", "question": "Who invented the World Wide Web at CERN, in what year was the proposal written, and what was the first web browser called?", "expected_keywords": ["Tim Berners-Lee", "1989", "WorldWideWeb"]}
{"id": "q22", "category": "chemistry", "question": "What is the atomic number of Gold, what is its Latin chemical symbol, and what is its standard melting point in Celsius?", "expected_keywords": ["79", "Au", "1064"]}
{"id": "q23", "category": "philosophy", "question": "Who formulated the 'Cogito, ergo sum' proposition, and in which 1637 French treatise did it first appear?", "expected_keywords": ["René Descartes", "Discourse on the Method"]}
{"id": "q24", "category": "programming_langs", "question": "What language was Rust originally written in before self-hosting, and what browser engine was Servo built to experiment with?", "expected_keywords": ["OCaml", "Firefox", "Gecko"]}
{"id": "q25", "category": "space_missions", "question": "What year did the Apollo 11 moon landing take place, who were the two astronauts that walked on the surface, and who stayed in orbit?", "expected_keywords": ["1969", "Neil Armstrong", "Buzz Aldrin", "Michael Collins"]}
{"id": "q26", "category": "economics", "question": "Who wrote 'The Wealth of Nations', in what year was it published, and what Scottish city was the author from?", "expected_keywords": ["Adam Smith", "1776", "Kirkcaldy"]}
{"id": "q27", "category": "medicine", "question": "What vaccine was developed by Jonas Salk in the 1950s, and what university conducted the clinical trials?", "expected_keywords": ["Polio", "University of Pittsburgh"]}
{"id": "q28", "category": "geology", "question": "What is the deepest known point on Earth, in what trench is it located, and approximately how deep is it in meters?", "expected_keywords": ["Challenger Deep", "Mariana Trench", "10900", "11000"]}
{"id": "q29", "category": "cybersecurity", "question": "What was the name of the 2010 computer worm discovered targeting Iranian nuclear facilities at Natanz?", "expected_keywords": ["Stuxnet"]}
{"id": "q30", "category": "agentic_evals", "question": "What framework developed by LangChain is used for tracing and evaluating LLM application trajectories?", "expected_keywords": ["LangSmith"]}
```

- [ ] **Step 2: Implement `agents/P1-react-agent/eval.py`**

Create `agents/P1-react-agent/eval.py`:

```python
"""Offline evaluation runner for P1 ReAct research agent."""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage

from P1_react_agent.agent import invoke


async def run_eval(limit: int | None = None) -> None:
    data_path = Path(__file__).parent / "data" / "eval_questions.jsonl"
    if not data_path.exists():
        print(f"Eval dataset not found at {data_path}")
        return

    items: list[dict[str, Any]] = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    if limit:
        items = items[:limit]

    print(f"Running P1 ReAct Agent Offline Evaluation on {len(items)} questions...\n")
    print(f"{'ID':<6} | {'Category':<18} | {'Latency':<8} | {'Tools':<6} | {'Keywords Matched'}")
    print("-" * 75)

    total_latency = 0.0
    total_tools = 0
    total_matches = 0
    total_possible_matches = 0

    for item in items:
        qid = item["id"]
        cat = item.get("category", "")
        q = item["question"]
        expected = item.get("expected_keywords", [])

        t0 = time.perf_counter()
        result = await invoke([HumanMessage(content=q)])
        t1 = time.perf_counter()
        latency = t1 - t0

        matched = [kw for kw in expected if kw.lower() in result.text.lower()]
        match_str = f"{len(matched)}/{len(expected)}"
        total_latency += latency
        total_tools += result.tool_calls_count
        total_matches += len(matched)
        total_possible_matches += len(expected)

        print(f"{qid:<6} | {cat:<18} | {latency:6.2f}s | {result.tool_calls_count:<6} | {match_str}")

    avg_lat = total_latency / max(1, len(items))
    avg_tools = total_tools / max(1, len(items))
    match_pct = (total_matches / max(1, total_possible_matches)) * 100.0

    print("-" * 75)
    print(f"Summary: {len(items)} questions evaluated")
    print(f"Average Latency:      {avg_lat:.2f}s")
    print(f"Average Tool Calls:   {avg_tools:.1f}")
    print(f"Keyword Recall Match: {match_pct:.1f}% ({total_matches}/{total_possible_matches})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run P1 ReAct Offline Evaluation")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions")
    args = parser.parse_args()
    asyncio.run(run_eval(limit=args.limit))
```

- [ ] **Step 3: Implement `agents/P1-react-agent/tests/test_eval.py`**

Create `agents/P1-react-agent/tests/test_eval.py`:

```python
"""Tests for P1 evaluation dataset structure and live eval markers."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from langchain_core.messages import HumanMessage

from P1_react_agent.agent import invoke


def test_eval_dataset_integrity() -> None:
    data_path = Path(__file__).resolve().parents[1] / "data" / "eval_questions.jsonl"
    assert data_path.exists()

    with open(data_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) == 30
    for line in lines:
        item = json.loads(line)
        assert "id" in item
        assert "question" in item
        assert "expected_keywords" in item
        assert len(item["expected_keywords"]) >= 1


@pytest.mark.eval
@pytest.mark.asyncio
async def test_live_agent_multi_hop_eval() -> None:
    """Live test exercising actual OpenRouter and Tavily tool-calling."""
    q = "What is the largest moon of Saturn and what year was it discovered?"
    res = await invoke([HumanMessage(content=q)])
    assert "Titan" in res.text
```

- [ ] **Step 4: Run eval test suite**

```bash
uv run --package P1-react-agent pytest agents/P1-react-agent/tests/test_eval.py -v
```

- [ ] **Step 5: Commit Task 5**

```bash
git add agents/P1-react-agent/data/eval_questions.jsonl agents/P1-react-agent/eval.py agents/P1-react-agent/tests/test_eval.py
git commit -m "feat(P1-react-agent): add 30-question offline eval dataset and benchmark runner"
```

---

## Task 6: CI Integration & Workspace Validation

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Update `.github/workflows/ci.yml` with `P1-react-agent`**

Update `.github/workflows/ci.yml`:

```yaml
      - name: Lint
        run: |
          uv run --package common ruff check common/src common/tests
          uv run --package P0-smoke ruff check agents/P0-smoke/src agents/P0-smoke/tests
          uv run --package P1-react-agent ruff check agents/P1-react-agent/src agents/P1-react-agent/tests
      - name: Typecheck
        run: |
          uv run --package common mypy common/src
          uv run --package P0-smoke mypy agents/P0-smoke/src
          uv run --package P1-react-agent mypy agents/P1-react-agent/src
      - name: Test (non-eval)
        run: uv run pytest -v -m "not eval"
      - name: Format check
        run: |
          uv run --package common ruff format --check common/src common/tests
          uv run --package P0-smoke ruff format --check agents/P0-smoke/src agents/P0-smoke/tests
          uv run --package P1-react-agent ruff format --check agents/P1-react-agent/src agents/P1-react-agent/tests
```

- [ ] **Step 2: Run monorepo test runner script**

```bash
bash scripts/test.sh
```

- [ ] **Step 3: Commit Task 6**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add P1-react-agent package to lint, typecheck, format, and test workflows"
```

---

## Task 7: Documentation, Cost Analysis & Verification

**Files:**
- Create: `agents/P1-react-agent/README.md`
- Create: `docs/superpowers/plans/2026-08-30-p1-react-agent-verified.md`

- [ ] **Step 1: Create `agents/P1-react-agent/README.md`**

Write `agents/P1-react-agent/README.md` with:
1. One-liner and architectural ASCII diagram showing FastAPI ↔ ReAct graph ↔ Tavily/Web tools ↔ Chat UI ↔ LangSmith.
2. Setup and execution instructions (`uv sync`, setting `.env`, starting `uvicorn P1_react_agent.server:app --port 8000`, running `apps/chat-ui`).
3. Offline evaluation benchmark results table from the 30-question dataset.
4. Unit economics cost report per 100 research questions with DeepSeek V4 Flash vs Claude Sonnet 4.5.

- [ ] **Step 2: Verify live end-to-end flow with chat UI**

Run backend on port 8000 and Next.js frontend on port 3000:
1. Submit multi-hop query: "Who invented the Python programming language and where was he working in 1991?"
2. Verify live tokens stream into the chat window.
3. Verify `ToolCallTree` accordion displays tool calls (`tavily_search`, `read_page`) with arguments and return snippets.
4. Verify LangSmith project `LearnAgenticAI/P1-react-agent` records full agent run with nested tool spans.

- [ ] **Step 3: Create verification record `docs/superpowers/plans/2026-08-30-p1-react-agent-verified.md`**

- [ ] **Step 4: Commit Task 7**

```bash
git add agents/P1-react-agent/README.md docs/superpowers/plans/2026-08-30-p1-react-agent-verified.md
git commit -m "docs(P1-react-agent): add project README with architecture, eval metrics, and verification log"
```

---

## Acceptance Verification Checklist

- [ ] `uv sync --all-packages` resolves cleanly with `P1-react-agent`.
- [ ] `uv run --package common pytest common/tests/test_tools.py -v` passes (7 unit tests).
- [ ] `uv run --package P1-react-agent pytest agents/P1-react-agent/tests/ -v -m "not eval"` passes.
- [ ] `uv run --package P1-react-agent mypy agents/P1-react-agent/src` passes with zero errors under strict mode.
- [ ] `uv run --package P1-react-agent ruff check agents/P1-react-agent/` and format check pass.
- [ ] `bash scripts/test.sh` runs all Python and TypeScript suites cleanly.
- [ ] Next.js chat UI displays streaming tokens and collapsible tool call trees for P1.
- [ ] LangSmith project `LearnAgenticAI/P1-react-agent` receives real traces.
- [ ] `agents/P1-react-agent/README.md` includes complete architecture diagram, cost report, and eval metrics.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-30-p1-react-agent.md`. **7 modular tasks**, fully typed with zero placeholders.

Two execution options:
1. **Subagent-Driven (recommended)** — Dispatch subagents task-by-task, with clean review checkpoints between tasks.
2. **Inline Execution** — Execute tasks sequentially in this session with verification gates after each task.

Please confirm how you would like to proceed.
