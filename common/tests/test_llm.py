"""Tests for common.llm — no live API calls; only config & routing."""

from __future__ import annotations

import pytest

from common.config import get_settings
from common.llm import get_model, model_id_for


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    get_settings.cache_clear()


def test_model_id_for_known_tasks() -> None:
    """All known tasks resolve to a string model id."""
    assert model_id_for("reasoning") == "deepseek/deepseek-v4-flash-0731"
    assert model_id_for("tools") == "openai/gpt-4o"
    assert model_id_for("local") == "ollama/llama-3.3-70b-versatile"
    assert model_id_for("judge") == "anthropic/claude-opus-4"
    assert model_id_for("cheap") == "openai/gpt-4o-mini"


def test_model_id_for_unknown_falls_back() -> None:
    """Unknown task name falls back to the reasoning default."""
    assert model_id_for("totally-unknown") == "deepseek/deepseek-v4-flash-0731"


def test_get_model_openrouter_route(monkeypatch: pytest.MonkeyPatch) -> None:
    """OpenRouter-routed tasks produce a ChatOpenAI pointing at OpenRouter."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    model = get_model("P1-react-agent", task="reasoning")
    assert model.model_name == "deepseek/deepseek-v4-flash-0731"  # type: ignore[attr-defined]
    assert str(model.openai_api_base).rstrip("/").endswith("/api/v1")  # type: ignore[attr-defined]
    assert model.openai_api_key.get_secret_value() == "sk-or-test"  # type: ignore[attr-defined]


def test_get_model_local_route(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ollama task routes to Ollama Cloud Pro via OpenAI-compatible API."""
    monkeypatch.setenv("OLLAMA_CLOUD_API_KEY", "ollama-test-key")
    model = get_model("P3-memory", task="local")
    assert model.model_name == "llama-3.3-70b-versatile"  # type: ignore[attr-defined]
    assert "ollama.com" in str(model.openai_api_base)  # type: ignore[attr-defined]


def test_get_model_missing_openrouter_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing OpenRouter key raises a clear error."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("OLLAMA_CLOUD_API_KEY", "set")
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        get_model("P1-react-agent", task="reasoning")


def test_get_model_missing_ollama_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing Ollama key raises a clear error."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "set")
    monkeypatch.setenv("OLLAMA_CLOUD_API_KEY", "")
    with pytest.raises(RuntimeError, match="OLLAMA_CLOUD_API_KEY"):
        get_model("P3-memory", task="local")
