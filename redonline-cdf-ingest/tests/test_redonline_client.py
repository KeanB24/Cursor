"""Tests for config-driven Red Online client (mock + HTTP)."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from redonline_cdf.redonline.client import RedOnlineClient

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


@pytest.fixture
def endpoints_config() -> dict:
    return {
        "auth": {"style": "bearer_header"},
        "defaults": {"timeout_seconds": 10, "page_size": 50},
        "endpoints": {
            "list_actions": {
                "method": "GET",
                "path": "/api/v1/actions",
                "query": {"pageSize": "{page_size}"},
                "since_param": "updatedSince",
                "items_path": "data.items",
                "pagination": {
                    "type": "page_token",
                    "next_token_path": "data.nextPageToken",
                    "token_param": "pageToken",
                },
                "fixture": "actions.json",
            }
        },
    }


def test_mock_fetch_actions(endpoints_config: dict) -> None:
    client = RedOnlineClient(
        endpoints_config=endpoints_config,
        mock=True,
        fixtures_dir=FIXTURES,
    )
    items = client.fetch_all("list_actions")
    assert len(items) == 2
    assert items[0]["id"] == "ACT-1001"
    client.close()


def test_http_fetch_with_bearer(endpoints_config: dict) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("Authorization") == "Bearer test-token"
        assert request.url.params.get("pageSize") == "50"
        assert request.url.params.get("updatedSince") == "2026-01-01T00:00:00Z"
        return httpx.Response(
            200,
            json={"data": {"items": [{"id": "A1", "title": "From API"}], "nextPageToken": None}},
        )

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    client = RedOnlineClient(
        base_url="https://api.example.com",
        token="test-token",
        endpoints_config=endpoints_config,
        mock=False,
        http_client=http,
    )
    items = client.fetch_all("list_actions", since="2026-01-01T00:00:00Z")
    assert items == [{"id": "A1", "title": "From API"}]
    client.close()


def test_page_token_pagination(endpoints_config: dict) -> None:
    pages = {
        None: {
            "data": {
                "items": [{"id": "1"}],
                "nextPageToken": "p2",
            }
        },
        "p2": {
            "data": {
                "items": [{"id": "2"}],
                "nextPageToken": None,
            }
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        token = request.url.params.get("pageToken")
        return httpx.Response(200, json=pages.get(token, pages[None]))

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    client = RedOnlineClient(
        base_url="https://api.example.com",
        token="t",
        endpoints_config=endpoints_config,
        mock=False,
        http_client=http,
    )
    items = client.fetch_all("list_actions")
    assert [i["id"] for i in items] == ["1", "2"]
    client.close()
