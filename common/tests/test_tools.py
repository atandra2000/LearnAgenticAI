"""Unit tests for shared search and web tools."""

from __future__ import annotations

import httpx
import pytest
import respx

from common.config import Settings
from common.tools.search import tavily_search
from common.tools.web import extract_clean_text, read_page


def test_extract_clean_text() -> None:
    html = """
    <html>
        <head><title>Test Page</title><style>body { color: red; }</style></head>
        <body>
            <script>console.log("ignore me");</script>
            <h1>Heading</h1>
            <p>First paragraph with <a href="#">link</a>.</p>
            <p>Second paragraph.</p>
        </body>
    </html>
    """
    cleaned = extract_clean_text(html)
    assert "Heading" in cleaned
    assert "First paragraph with link." in cleaned
    assert "Second paragraph." in cleaned
    assert "console.log" not in cleaned
    assert "color: red" not in cleaned


@pytest.mark.asyncio
async def test_tavily_search_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "common.tools.search.get_settings",
        lambda: Settings(tavily_api_key=""),
    )
    result = await tavily_search.ainvoke({"query": "LangGraph"})
    assert "Error executing web search" in result
    assert "TAVILY_API_KEY is not set" in result


@pytest.mark.asyncio
@respx.mock
async def test_tavily_search_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "common.tools.search.get_settings",
        lambda: Settings(tavily_api_key="mock-key"),
    )
    mock_payload = {
        "results": [
            {
                "title": "LangGraph Documentation",
                "url": "https://langchain-ai.github.io/langgraph/",
                "content": "LangGraph is a library for building stateful, multi-actor applications with LLMs.",
            }
        ]
    }
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(200, json=mock_payload)
    )

    result = await tavily_search.ainvoke({"query": "LangGraph", "max_results": 1})
    assert "[1] LangGraph Documentation" in result
    assert "https://langchain-ai.github.io/langgraph/" in result
    assert "LangGraph is a library" in result


@pytest.mark.asyncio
@respx.mock
async def test_tavily_search_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "common.tools.search.get_settings",
        lambda: Settings(tavily_api_key="mock-key"),
    )
    respx.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )
    result = await tavily_search.ainvoke({"query": "LangGraph"})
    assert "Search error: Tavily search API returned HTTP 500" in result


@pytest.mark.asyncio
async def test_read_page_invalid_scheme() -> None:
    result = await read_page.ainvoke({"url": "ftp://example.com/file.txt"})
    assert "Invalid URL scheme" in result


@pytest.mark.asyncio
@respx.mock
async def test_read_page_success() -> None:
    respx.get("https://example.com/doc").mock(
        return_value=httpx.Response(
            200,
            text="<html><body><h1>Doc Title</h1><p>Detailed technical content.</p></body></html>",
            headers={"content-type": "text/html"},
        )
    )
    result = await read_page.ainvoke({"url": "https://example.com/doc"})
    assert "Doc Title" in result
    assert "Detailed technical content." in result


@pytest.mark.asyncio
@respx.mock
async def test_read_page_truncation() -> None:
    long_content = "A" * 500
    respx.get("https://example.com/long").mock(
        return_value=httpx.Response(
            200,
            text=f"<html><body><p>{long_content}</p></body></html>",
            headers={"content-type": "text/html"},
        )
    )
    result = await read_page.ainvoke({"url": "https://example.com/long", "max_chars": 100})
    assert len(result) > 100
    assert "[Content truncated at 100 characters]" in result


@pytest.mark.asyncio
@respx.mock
async def test_read_page_404_error() -> None:
    respx.get("https://example.com/notfound").mock(
        return_value=httpx.Response(404, text="Not Found")
    )
    result = await read_page.ainvoke({"url": "https://example.com/notfound"})
    assert "Error fetching https://example.com/notfound: HTTP 404" in result
