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
        "auth": {
            "style": "header",
            "header_name": "X-ROL-API-KEY",
            "api_key": "test-api-key",
        },
        "defaults": {
            "timeout_seconds": 10,
            "page_size": 50,
            "site_id": "112087",
            "user_id": "584646",
        },
        "endpoints": {
            "list_sites": {
                "method": "GET",
                "path": "/v2/secure-clients/legapi-general/sites",
                "query": {},
                "items_path": "sites",
                "pagination": {"type": "none"},
                "fixture": "sites.json",
            },
            "list_users_by_site": {
                "method": "GET",
                "path": "/v2/secure-clients/legapi-general/users/sites/{site_id}",
                "path_params": {"site_id": "{site_id}"},
                "query": {},
                "items_path": "users",
                "pagination": {"type": "none"},
                "fixture": "users.json",
            },
            "list_tasks_by_user": {
                "method": "GET",
                "path": "/v2/secure-clients/tasks",
                "query": {"user_id": "{user_id}"},
                "items_path": "data",
                "pagination": {"type": "none"},
                "fixture": "tasks.json",
            },
        },
    }


def test_resolve_verify_ssl_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from redonline_cdf.redonline.client import resolve_verify_ssl

    monkeypatch.delenv("REDONLINE_VERIFY_SSL", raising=False)
    assert resolve_verify_ssl() is True
    monkeypatch.setenv("REDONLINE_VERIFY_SSL", "0")
    assert resolve_verify_ssl() is False
    assert resolve_verify_ssl(True) is True
    assert resolve_verify_ssl(False) is False


def test_mock_fetch_sites(endpoints_config: dict) -> None:
    client = RedOnlineClient(
        endpoints_config=endpoints_config,
        mock=True,
        fixtures_dir=FIXTURES,
    )
    items = client.fetch_all("list_sites")
    assert len(items) == 2
    assert items[0]["id_site"] == 112084
    client.close()


def test_http_fetch_with_api_key_header(endpoints_config: dict) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-ROL-API-KEY") == "test-api-key"
        assert "/users/sites/112087" in str(request.url)
        return httpx.Response(
            200,
            json={"users": [{"id_user": 1, "email": "a@b.com"}]},
        )

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    client = RedOnlineClient(
        base_url="https://apigw.ct-test.hse-compliance.net",
        token="test-api-key",
        endpoints_config=endpoints_config,
        mock=False,
        http_client=http,
    )
    items = client.fetch_all("list_users_by_site")
    assert items == [{"id_user": 1, "email": "a@b.com"}]
    client.close()


def test_tasks_query_user_id(endpoints_config: dict) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("user_id") == "999"
        assert request.headers.get("X-ROL-API-KEY") == "test-api-key"
        return httpx.Response(200, json={"data": [{"id": 10, "title": "T"}]})

    transport = httpx.MockTransport(handler)
    http = httpx.Client(transport=transport)
    client = RedOnlineClient(
        base_url="https://apigw.example.com",
        token="test-api-key",
        endpoints_config=endpoints_config,
        mock=False,
        http_client=http,
    )
    items = client.fetch_all(
        "list_tasks_by_user",
        path_vars={"user_id": "999"},
    )
    assert items == [{"id": 10, "title": "T"}]
    client.close()
