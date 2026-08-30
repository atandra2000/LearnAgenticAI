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
