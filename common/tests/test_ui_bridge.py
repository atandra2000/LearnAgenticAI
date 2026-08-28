"""Tests for common.ui_bridge."""

from __future__ import annotations

import json

import pytest

from common.ui_bridge import (
    VALID_EVENT_TYPES,
    error_event,
    message_end_event,
    to_sse,
    token_event,
    tool_end_event,
    tool_start_event,
    trace_meta_event,
)


def test_to_sse_format() -> None:
    """SSE wire format is `event: X\\ndata: Y\\n\\n`."""
    out = to_sse("token", {"content": "hi"})
    assert out == b'event: token\ndata: {"content":"hi"}\n\n'


def test_to_sse_rejects_unknown_event_type() -> None:
    """Unknown event types raise ValueError with a helpful message."""
    with pytest.raises(ValueError, match="Unknown event_type"):
        to_sse("nonsense", {})


def test_valid_event_types_is_closed() -> None:
    """All helper functions use one of the closed set of event types."""
    expected = {"token", "tool_start", "tool_end", "message_end", "error", "trace_meta"}
    assert VALID_EVENT_TYPES == expected


def test_token_event_payload() -> None:
    """token_event wraps content into a dict."""
    out = token_event("hello world")
    assert out.startswith(b"event: token\ndata: ")
    # Body is valid JSON containing the content
    body = out.split(b"data: ", 1)[1].split(b"\n\n")[0]
    assert json.loads(body) == {"content": "hello world"}


def test_tool_start_event_payload() -> None:
    """tool_start_event includes name, args, call_id."""
    out = tool_start_event("web_search", {"q": "weather"}, call_id="abc-123")
    body = out.split(b"data: ", 1)[1].split(b"\n\n")[0]
    assert json.loads(body) == {
        "tool_name": "web_search",
        "args": {"q": "weather"},
        "call_id": "abc-123",
    }


def test_tool_end_event_payload() -> None:
    """tool_end_event returns call_id + result."""
    out = tool_end_event("abc-123", result={"status": "ok"})
    body = out.split(b"data: ", 1)[1].split(b"\n\n")[0]
    assert json.loads(body) == {"call_id": "abc-123", "result": {"status": "ok"}}


def test_message_end_event_default() -> None:
    """message_end_event defaults finish_reason to 'stop'."""
    out = message_end_event()
    body = out.split(b"data: ", 1)[1].split(b"\n\n")[0]
    assert json.loads(body) == {"finish_reason": "stop"}


def test_error_event_payload() -> None:
    """error_event uses default code 'agent_error' unless overridden."""
    out = error_event("boom", code="llm_timeout")
    body = out.split(b"data: ", 1)[1].split(b"\n\n")[0]
    assert json.loads(body) == {"message": "boom", "code": "llm_timeout"}


def test_trace_meta_event_payload() -> None:
    """trace_meta_event includes run_url and run_id."""
    out = trace_meta_event("https://smith.example/r/abc", "abc")
    body = out.split(b"data: ", 1)[1].split(b"\n\n")[0]
    assert json.loads(body) == {
        "run_url": "https://smith.example/r/abc",
        "run_id": "abc",
    }
