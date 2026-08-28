"""Echo agent for P0 — the simplest possible LangChain chat model call."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from common.llm import get_model
from common.ui_bridge import (
    message_end_event,
    token_event,
    trace_meta_event,
)
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.runnables import Runnable

SYSTEM_PROMPT = (
    "You are a friendly echo agent. Reply to the user's message with a brief, "
    "warm response that acknowledges what they said. If they ask a question, "
    "answer it concisely in one or two sentences."
)


@dataclass
class EchoResult:
    """A single turn's worth of generated text + LangSmith run id."""

    text: str
    run_id: str


def build_agent() -> Runnable[Any, Any]:
    """Return a runnable that takes a list of messages and returns one."""
    model = get_model("P0-smoke", task="reasoning")
    return model


async def stream_agent(messages: list[BaseMessage], run_id: str) -> AsyncIterator[bytes]:
    """Stream an agent response as SSE events.

    Yields `token` events as the model generates, then `message_end`, then
    `trace_meta` pointing at the LangSmith run.
    """
    model = build_agent()
    full: list[str] = []
    # LangChain's .astream yields chunks. Each chunk has .content.
    async for chunk in model.astream([SystemMessage(content=SYSTEM_PROMPT), *messages]):
        content = getattr(chunk, "content", "")
        if content:
            full.append(content)
            yield token_event(content)
    yield message_end_event("stop")
    yield trace_meta_event(
        run_url=f"https://smith.langchain.com/r/{run_id}",
        run_id=run_id,
    )


async def invoke(messages: list[BaseMessage]) -> EchoResult:
    """Non-streaming single-shot invoke — used by tests."""
    model = build_agent()
    response = await model.ainvoke([SystemMessage(content=SYSTEM_PROMPT), *messages])
    return EchoResult(text=response.content, run_id="not-traced")
