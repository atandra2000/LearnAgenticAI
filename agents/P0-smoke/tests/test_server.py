"""Tests for the FastAPI server — uses TestClient, no live LLM calls."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from P0_smoke.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_request_validation_empty_messages(client: TestClient) -> None:
    """Empty messages list is rejected with 422."""
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [], "stream": True},
    )
    assert response.status_code == 422


def test_request_validation_missing_field(client: TestClient) -> None:
    """Missing `messages` field is rejected with 422."""
    response = client.post(
        "/v1/chat/completions",
        json={"stream": True},
    )
    assert response.status_code == 422


@pytest.mark.eval
def test_endpoint_accepts_well_formed_request(client: TestClient) -> None:
    """A well-formed request returns 200 + text/event-stream content type.

    Eval-marked: the first stream chunk only arrives after the real
    OpenRouter call, so this test makes a live API call when a key is
    present and must not run under `pytest -m "not eval"`.
    """
    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        # Read at least one chunk to confirm the stream is open
        # We don't fully consume because that would invoke the real LLM.
        for _ in response.iter_text():
            break
