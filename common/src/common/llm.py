"""Multi-provider LLM factory.

The portfolio's routing rule (spec §5, amended by user directive 2026-08-29):
    - heavy reasoning (P1, P4, P7)  -> deepseek/deepseek-v4-flash-0731
    - tool-heavy (P2, P5, P8)       -> openai/gpt-4o
    - local/memory (P3, P6)         -> ollama/llama-3.3-70b
    - judge (P9)                    -> anthropic/claude-opus-4
    - cheap expansion (P9)          -> openai/gpt-4o-mini

`task` is a free-form string ("reasoning", "tools", "local", "judge", "cheap")
and an unknown task falls back to the reasoning default.
"""

from __future__ import annotations

from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from common.config import get_settings

TaskName = Literal["reasoning", "tools", "local", "judge", "cheap"]

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# (provider, model_id) per task.  OpenRouter keys are 'provider/model'.
_MODEL_TABLE: dict[TaskName, tuple[str, str]] = {
    "reasoning": ("deepseek", "deepseek-v4-flash-0731"),
    "tools": ("openai", "gpt-4o"),
    "local": ("ollama", "llama-3.3-70b-versatile"),
    "judge": ("anthropic", "claude-opus-4"),
    "cheap": ("openai", "gpt-4o-mini"),
}


def get_model(
    project: str,
    task: TaskName | str = "reasoning",
    max_tokens: int = 1024,
) -> BaseChatModel:
    """Return a LangChain chat model for a (project, task) pair.

    Args:
        project: Agent slug (e.g., "P1-react-agent"). Used to label traces
                 via LangSmith metadata; not the model routing key.
        task: One of "reasoning", "tools", "local", "judge", "cheap".
              Unknown tasks fall back to "reasoning".
        max_tokens: Output cap sent with each request. OpenRouter defaults
              to the model's full output budget when unset and rejects
              (402) requests whose budget exceeds the remaining credits —
              so a sane explicit cap is set per call.

    Returns:
        A configured BaseChatModel. All models are routed through
        OpenRouter except the local Ollama path.
    """
    if task not in _MODEL_TABLE:
        task = "reasoning"
    provider, model_id = _MODEL_TABLE[task]
    settings = get_settings()

    # Local path: use Ollama Cloud Pro via OpenAI-compatible API
    if provider == "ollama":
        if not settings.ollama_cloud_api_key:
            raise RuntimeError(
                "OLLAMA_CLOUD_API_KEY is not set. Set it in .env to use the 'local' task."
            )
        return ChatOpenAI(
            model=model_id,
            base_url="https://ollama.com/v1",
            api_key=settings.ollama_cloud_api_key,
            temperature=0,
            max_tokens=max_tokens,
            max_retries=2,
        )

    # All other tasks route through OpenRouter (OpenAI-compatible)
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Set it in .env to use OpenRouter-routed tasks."
        )
    return ChatOpenAI(
        model=f"{provider}/{model_id}",
        base_url=_OPENROUTER_BASE,
        api_key=settings.openrouter_api_key,
        temperature=0,
        max_tokens=max_tokens,
        max_retries=2,
    )


def model_id_for(task: TaskName | str) -> str:
    """Return the raw model id for a task (useful for cost reports)."""
    if task not in _MODEL_TABLE:
        task = "reasoning"
    provider, model_id = _MODEL_TABLE[task]
    return f"{provider}/{model_id}"
