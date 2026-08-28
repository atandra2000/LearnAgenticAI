"""Tests for common.tracing."""

from __future__ import annotations

import os

import pytest

from common.config import get_settings
from common.tracing import current_project, setup


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    """Ensure a fresh Settings per test (so monkeypatched env wins)."""
    get_settings.cache_clear()


def test_setup_sets_project(monkeypatch: pytest.MonkeyPatch) -> None:
    """setup() writes LANGSMITH_PROJECT to the prefixed name."""
    monkeypatch.setenv("LANGSMITH_PROJECT", "")
    with setup("P1-react-agent"):
        assert os.environ["LANGSMITH_PROJECT"] == "LearnAgenticAI/P1-react-agent"
        assert os.environ["LANGSMITH_TRACING"] == "true"
    # Restored after the block
    assert os.environ.get("LANGSMITH_PROJECT", "") == ""


def test_setup_restores_previous_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """setup() restores the prior env on exit."""
    monkeypatch.setenv("LANGSMITH_PROJECT", "OldProject")
    with setup("P2-rag"):
        assert os.environ["LANGSMITH_PROJECT"] == "LearnAgenticAI/P2-rag"
    assert os.environ["LANGSMITH_PROJECT"] == "OldProject"


def test_current_project_returns_set_value() -> None:
    """current_project() reflects what setup() left behind (or nothing)."""
    os.environ.pop("LANGSMITH_PROJECT", None)
    assert current_project() is None
    with setup("P9-evals"):
        assert current_project() == "LearnAgenticAI/P9-evals"


def test_setup_uses_custom_prefix(monkeypatch: pytest.MonkeyPatch) -> None:
    """Custom LANGSMITH_PROJECT_PREFIX is respected."""
    monkeypatch.setenv("LANGSMITH_PROJECT_PREFIX", "MyPrefix")
    get_settings.cache_clear()
    with setup("P3-memory"):
        assert os.environ["LANGSMITH_PROJECT"] == "MyPrefix/P3-memory"
