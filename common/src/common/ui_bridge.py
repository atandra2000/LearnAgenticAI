"""SSE event schema shared by agent backends and the chat UI.

The chat UI (`apps/chat-ui/`) parses the event stream produced by every
agent's FastAPI `/v1/chat/completions` endpoint. Keeping the schema here
ensures every agent speaks the same wire format.

SSE wire format:
    event: <event_type>
    data: <json>

Blank line terminates an event.
"""

from __future__ import annotations

import json
from typing import Any, Literal

# --- Event types (closed enum) ---
EventType = Literal[
    "token",  # streaming LLM token
    "tool_start",  # tool invocation beginning
    "tool_end",  # tool invocation complete with result
    "message_end",  # assistant message complete
    "error",  # unrecoverable error
    "trace_meta",  # langsmith run URL for the message
]

VALID_EVENT_TYPES: frozenset[str] = frozenset(
    {"token", "tool_start", "tool_end", "message_end", "error", "trace_meta"}
)


def to_sse(event_type: str, data: dict[str, Any]) -> bytes:
    """Serialize an event as a single SSE message.

    Args:
        event_type: One of `VALID_EVENT_TYPES`.
        data: JSON-serializable dict. Will be serialized with `json.dumps`.

    Returns:
        Bytes ready to yield from a StreamingResponse.

    Raises:
        ValueError: If `event_type` is not a known event type.
    """
    if event_type not in VALID_EVENT_TYPES:
        raise ValueError(
            f"Unknown event_type {event_type!r}. Expected one of {sorted(VALID_EVENT_TYPES)}"
        )
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_type}\ndata: {payload}\n\n".encode()


def token_event(content: str) -> bytes:
    """SSE event: a single streamed token from the LLM."""
    return to_sse("token", {"content": content})


def tool_start_event(tool_name: str, args: dict[str, Any], call_id: str) -> bytes:
    """SSE event: a tool invocation has begun."""
    return to_sse(
        "tool_start",
        {"tool_name": tool_name, "args": args, "call_id": call_id},
    )


def tool_end_event(call_id: str, result: Any) -> bytes:
    """SSE event: a tool invocation has returned."""
    return to_sse("tool_end", {"call_id": call_id, "result": result})


def message_end_event(finish_reason: str = "stop") -> bytes:
    """SSE event: the assistant message is complete."""
    return to_sse("message_end", {"finish_reason": finish_reason})


def error_event(message: str, code: str = "agent_error") -> bytes:
    """SSE event: an unrecoverable error occurred."""
    return to_sse("error", {"message": message, "code": code})


def trace_meta_event(run_url: str, run_id: str) -> bytes:
    """SSE event: link to the LangSmith trace for this assistant message."""
    return to_sse("trace_meta", {"run_url": run_url, "run_id": run_id})
