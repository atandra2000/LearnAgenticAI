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

    with open(data_path, encoding="utf-8") as f:
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
