"""LangSmith tracing helpers.

Usage in an agent:
    from common.tracing import setup

    with setup("P1-react-agent"):
        agent.invoke({"messages": [...]})  # auto-traced
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from common.config import get_settings


@contextmanager
def setup(slug: str) -> Iterator[None]:
    """Wire LangSmith env vars for the duration of a `with` block.

    Args:
        slug: Short name for this agent (e.g., "P1-react-agent").
              Resolves to LangSmith project "{prefix}/{slug}".

    Yields:
        None. Caller runs agent code inside the `with` block.
    """
    cfg = get_settings()  # resolved per-call so cache_clear()/env changes take effect
    project = cfg.project_name(slug)
    previous = {
        "LANGSMITH_TRACING": os.environ.get("LANGSMITH_TRACING"),
        "LANGSMITH_ENDPOINT": os.environ.get("LANGSMITH_ENDPOINT"),
        "LANGSMITH_API_KEY": os.environ.get("LANGSMITH_API_KEY"),
        "LANGSMITH_PROJECT": os.environ.get("LANGSMITH_PROJECT"),
    }
    try:
        os.environ["LANGSMITH_TRACING"] = "true" if cfg.langsmith_tracing else "false"
        os.environ["LANGSMITH_ENDPOINT"] = cfg.langsmith_endpoint
        if cfg.langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = cfg.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = project
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def current_project() -> str | None:
    """Return the active LangSmith project, or None if not set."""
    return os.environ.get("LANGSMITH_PROJECT")
