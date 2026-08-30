"""Web page content reader tool for deep text extraction."""

from __future__ import annotations

import re
from html.parser import HTMLParser

import httpx
from langchain_core.tools import tool


class _HTMLTextExtractor(HTMLParser):
    """Minimal HTML parser that extracts text while omitting scripts, styles, and tags."""

    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._ignore: bool = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._ignore = True
        elif tag.lower() in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr", "br"):
            self._pieces.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style", "noscript", "svg", "header", "footer", "nav"):
            self._ignore = False
        elif tag.lower() in ("p", "div", "h1", "h2", "h3", "h4", "li", "tr"):
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._ignore:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        # Collapse excessive whitespace
        cleaned = re.sub(r"[ \t]+", " ", raw)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()


def extract_clean_text(html_content: str) -> str:
    """Convert raw HTML into readable plain text."""
    parser = _HTMLTextExtractor()
    parser.feed(html_content)
    return parser.get_text()


@tool
async def read_page(url: str, max_chars: int = 4000) -> str:
    """Fetch a webpage by URL and return its readable text content.

    Use this tool when search snippets are insufficient and you need to inspect
    the full content of an article, documentation page, or reference link.

    Args:
        url: The complete HTTP/HTTPS URL of the page to read.
        max_chars: Maximum characters to return (default: 4000).

    Returns:
        Clean plain text content extracted from the webpage.
    """
    if not url.startswith(("http://", "https://")):
        return f"Error: Invalid URL scheme for {url!r}. Must start with http:// or https://"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,text/plain",
    }

    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True, verify=True) as client:
            response = await client.get(url, headers=headers)
            if response.status_code >= 400:
                return f"Error fetching {url}: HTTP {response.status_code}"

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" in content_type or "application/xhtml" in content_type:
                text = extract_clean_text(response.text)
            else:
                text = response.text.strip()

            if not text:
                return f"Notice: Webpage at {url} returned empty readable text."

            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... [Content truncated at {max_chars} characters]"

            return text
    except httpx.TimeoutException:
        return f"Error: Request timed out while fetching {url}"
    except httpx.RequestError as e:
        return f"Error: Network failure while connecting to {url}: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Error: Unexpected failure reading {url}: {e}"
