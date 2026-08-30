"""Tests for P1 ReAct agent graph building and streaming events."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import HumanMessage

from P1_react_agent.agent import build_agent, invoke, stream_agent


class FakeToolChatModel(FakeListChatModel):
    """Fake chat model that supports tool binding for LangGraph."""

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self


def test_build_agent_compiles() -> None:
    fake_model = FakeToolChatModel(responses=["Hello from fake agent!"])
    agent = build_agent(model_override=fake_model)
    assert agent is not None


@pytest.mark.asyncio
async def test_agent_invoke_simple() -> None:
    fake_model = FakeToolChatModel(responses=["LangGraph is stateful."])
    result = await invoke(
        [HumanMessage(content="What is LangGraph?")],
        model_override=fake_model,
    )
    assert result.text == "LangGraph is stateful."
    assert result.tool_calls_count == 0


@pytest.mark.asyncio
async def test_stream_agent_emits_expected_sse_structure() -> None:
    fake_model = FakeToolChatModel(responses=["DeepSeek is fast."])
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
