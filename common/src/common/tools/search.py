"""Web search tool wrapping the Tavily REST API."""

from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool

from common.config import get_settings

_TAVILY_API_URL = "https://api.tavily.com/search"


async def _execute_tavily_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Internal helper to execute a raw search against Tavily."""
    settings = get_settings()
    if not settings.tavily_api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Set it in .env to use the tavily_search tool."
        )

    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max(1, min(max_results, 10)),
        "include_answer": False,
        "include_raw_content": False,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(_TAVILY_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            return {
                "error": f"Tavily search API returned HTTP {response.status_code}: {response.text}"
            }
        data: dict[str, Any] = response.json()
        return data


@tool
async def tavily_search(query: str, max_results: int = 5) -> str:
    """Search the public web for real-time information, facts, news, or technical documentation.

    Args:
        query: The search query string.
        max_results: Maximum number of search results to return (default: 5).

    Returns:
        A structured string of search results containing titles, URLs, and text snippets.
    """
    try:
        data = await _execute_tavily_search(query, max_results=max_results)
    except Exception as e:  # noqa: BLE001
        return f"Error executing web search: {e}"

    if "error" in data:
        return f"Search error: {data['error']}"

    results = data.get("results", [])
    if not results:
        return f"No search results found for query: {query!r}"

    formatted_parts: list[str] = []
    for idx, item in enumerate(results, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        content = item.get("content", "").strip()
        formatted_parts.append(f"[{idx}] {title}\nURL: {url}\nSnippet: {content}")

    return "\n\n".join(formatted_parts)
