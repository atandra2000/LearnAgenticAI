"""Typed process configuration loaded from env + .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All shared configuration. Loaded once at process start."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[3] / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM providers ---
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key (direct)")
    openai_api_key: str = Field(default="", description="OpenAI API key (direct)")
    ollama_cloud_api_key: str = Field(default="", description="Ollama Cloud Pro API key")

    # --- LangSmith ---
    langsmith_api_key: str = Field(default="")
    langsmith_tracing: bool = Field(default=True)
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com")
    langsmith_project_prefix: str = Field(default="LearnAgenticAI")

    # --- Database / Vector store ---
    database_url: str = Field(default="postgresql://agentic:agentic@localhost:5432/agentic")
    qdrant_url: str = Field(default="http://localhost:6333")
    qdrant_api_key: str = Field(default="")

    def project_name(self, slug: str) -> str:
        """Return a fully-qualified LangSmith project name for an agent."""
        return f"{self.langsmith_project_prefix}/{slug}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()


# Module-level singleton for convenience
settings = get_settings()
