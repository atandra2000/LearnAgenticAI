"""Tests for P1 FastAPI server request validation and streaming endpoints."""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from P1_react_agent.server import ChatMessage, _to_langchain_messages, app

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


def test_to_langchain_messages() -> None:
    items = [
        ChatMessage(role="system", content="System instruction"),
        ChatMessage(role="user", content="User prompt"),
        ChatMessage(role="assistant", content="Assistant reply"),
    ]
    messages = _to_langchain_messages(items)
    assert len(messages) == 3
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == "System instruction"
    assert isinstance(messages[1], HumanMessage)
    assert messages[1].content == "User prompt"
    assert isinstance(messages[2], AIMessage)
    assert messages[2].content == "Assistant reply"


def test_chat_completions_streaming() -> None:
    async def mock_stream(messages: list[object], run_id: str):
        yield b'event: token\ndata: {"delta": "hello"}\n\n'
        yield b'event: message_end\ndata: {"finish_reason": "stop"}\n\n'

    with patch("P1_react_agent.server.stream_agent", side_effect=mock_stream):
        res = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        body = res.text
        assert "event: token" in body
        assert "event: message_end" in body


def test_chat_completions_error_handling() -> None:
    async def mock_stream_error(messages: list[object], run_id: str):
        raise RuntimeError("Agent failed")
        yield b""  # unreachable generator yield

    with patch("P1_react_agent.server.stream_agent", side_effect=mock_stream_error):
        res = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "hello"}]},
        )
        assert res.status_code == 200
        body = res.text
        assert "event: error" in body
        assert "Agent failed" in body
