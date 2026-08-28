"""Tests for common.config.Settings."""

from __future__ import annotations

import pytest

from common.config import Settings, get_settings


def test_settings_defaults() -> None:
    """Settings load with sensible defaults when no env vars are set."""
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.langsmith_tracing is True
    assert s.langsmith_endpoint == "https://api.smith.langchain.com"
    assert s.langsmith_project_prefix == "LearnAgenticAI"
    assert s.database_url.startswith("postgresql://")


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Env vars override defaults."""
    monkeypatch.setenv("LANGSMITH_PROJECT_PREFIX", "CustomPrefix")
    monkeypatch.setenv("DATABASE_URL", "postgresql://override:override@h:5432/d")
    # Clear the lru_cache so a fresh Settings is built
    get_settings.cache_clear()
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.langsmith_project_prefix == "CustomPrefix"
    assert s.database_url == "postgresql://override:override@h:5432/d"


def test_project_name_helper() -> None:
    """project_name() composes prefix + slug."""
    s = Settings(_env_file=None)  # type: ignore[call-arg]
    assert s.project_name("P1-react-agent") == "LearnAgenticAI/P1-react-agent"


def test_get_settings_is_cached() -> None:
    """get_settings returns the same instance on repeat calls."""
    get_settings.cache_clear()
    a = get_settings()
    b = get_settings()
    assert a is b
