"""ReAct Research Agent implementation using LangGraph and LangChain tools."""

from __future__ import annotations

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


def build_agent(
    model_override: BaseChatModel | None = None,
) -> CompiledStateGraph[Any, Any, Any, Any]:
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
            if (
                chunk
                and hasattr(chunk, "content")
                and isinstance(chunk.content, str)
                and chunk.content
            ):
                yield token_event(chunk.content)

        # 2. Stream tool start telemetry
        elif event_kind == "on_tool_start":
            tool_name = str(event.get("name", "unknown_tool"))
            tool_run_id = str(event.get("run_id", run_id))
            event_data: Any = event.get("data") or {}
            raw_input: Any = event_data.get("input", {})
            args = raw_input if isinstance(raw_input, dict) else {"input": str(raw_input)}
            yield tool_start_event(tool_name=tool_name, args=args, call_id=tool_run_id)

        # 3. Stream tool end telemetry
        elif event_kind == "on_tool_end":
            tool_run_id = str(event.get("run_id", run_id))
            event_data_end: Any = event.get("data") or {}
            raw_output: Any = event_data_end.get("output")
            result: Any = raw_output
            if raw_output is not None and hasattr(raw_output, "content"):
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
