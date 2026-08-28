"""Tests for P0 agent logic (no live LLM calls)."""

from __future__ import annotations

import pytest
from common.ui_bridge import VALID_EVENT_TYPES
from langchain_core.messages import HumanMessage

from P0_smoke.agent import build_agent, invoke, stream_agent

# Mark all tests in this module as 'eval' so CI can skip without API keys
pytestmark = pytest.mark.eval


@pytest.mark.asyncio
async def test_stream_agent_emits_expected_events() -> None:
    """stream_agent yields token, message_end, and trace_meta events."""
    events: list[bytes] = []
    async for ev in stream_agent([HumanMessage(content="hi")], run_id="abc"):
        events.append(ev)
    assert len(events) >= 2  # at least one token + message_end
    decoded = [ev.decode("utf-8") for ev in events]
    assert any(ev.startswith("event: message_end") for ev in decoded)
    assert any(ev.startswith("event: trace_meta") for ev in decoded)


@pytest.mark.asyncio
async def test_invoke_returns_text_and_run_id() -> None:
    """invoke returns text content and a run id placeholder."""
    result = await invoke([HumanMessage(content="hello")])
    assert isinstance(result.text, str)
    assert result.run_id == "not-traced"


def test_build_agent_returns_runnable() -> None:
    """build_agent returns a LangChain Runnable."""
    agent = build_agent()
    assert hasattr(agent, "invoke")
    assert hasattr(agent, "astream")


def test_valid_event_types_includes_required() -> None:
    """The shared SSE schema includes the events P0 emits."""
    assert {"token", "message_end", "trace_meta"}.issubset(VALID_EVENT_TYPES)
