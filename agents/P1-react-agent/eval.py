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


def load_eval_questions(path: Path) -> list[dict[str, Any]]:
    """Load evaluation questions from a JSONL file."""
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))
    return items


async def run_eval(limit: int | None = None) -> None:
    data_path = Path(__file__).parent / "data" / "eval_questions.jsonl"
    items = load_eval_questions(data_path)
    if not items:
        print(f"Eval dataset not found or empty at {data_path}")
        return

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
        expected: list[str] = item.get("expected_keywords", [])

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

        print(
            f"{qid:<6} | {cat:<18} | {latency:6.2f}s | {result.tool_calls_count:<6} | {match_str}"
        )

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
