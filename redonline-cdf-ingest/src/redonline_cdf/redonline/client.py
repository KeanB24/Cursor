"""Config-driven Red Online REST client with pagination and mock/fixture mode."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Iterator

import httpx

from redonline_cdf.config import load_endpoints, project_root

logger = logging.getLogger(__name__)


def dig(data: Any, path: str | None) -> Any:
    """Resolve a dotted path like 'data.items' against nested dicts."""
    if not path:
        return data
    current = data
    for part in path.split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


class RedOnlineClient:
    """Fetch paginated entity lists from Red Online using endpoints.yaml."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        endpoints_config: dict[str, Any] | None = None,
        mock: bool | None = None,
        fixtures_dir: Path | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = endpoints_config or load_endpoints()
        self.base_url = (base_url or os.getenv("REDONLINE_BASE_URL", "")).rstrip("/")
        self.token = token
        self.mock = (
            mock
            if mock is not None
            else os.getenv("REDONLINE_MOCK", "0").lower() in {"1", "true", "yes"}
        )
        self.fixtures_dir = fixtures_dir or (project_root() / "fixtures")
        self._owns_http = http_client is None
        self._http = http_client or httpx.Client(timeout=self._timeout())

    def _timeout(self) -> float:
        defaults = self._config.get("defaults") or {}
        return float(defaults.get("timeout_seconds", 60))

    def _page_size(self) -> int:
        defaults = self._config.get("defaults") or {}
        return int(defaults.get("page_size", 100))

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def __enter__(self) -> RedOnlineClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _auth_headers_and_params(self) -> tuple[dict[str, str], dict[str, str]]:
        auth = self._config.get("auth") or {}
        style = auth.get("style", "bearer_header")
        headers: dict[str, str] = {"Accept": "application/json"}
        params: dict[str, str] = {}
        if not self.token:
            return headers, params
        if style == "bearer_header":
            headers["Authorization"] = f"Bearer {self.token}"
        elif style == "header":
            name = auth.get("header_name", "Authorization")
            headers[str(name)] = self.token
        elif style == "query":
            params[str(auth.get("query_param", "access_token"))] = self.token
        else:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers, params

    def _endpoint(self, name: str) -> dict[str, Any]:
        endpoints = self._config.get("endpoints") or {}
        if name not in endpoints:
            raise KeyError(f"Unknown endpoint '{name}' in endpoints.yaml")
        return endpoints[name]

    def _load_fixture(self, endpoint: dict[str, Any]) -> dict[str, Any]:
        fixture_name = endpoint.get("fixture")
        if not fixture_name:
            raise RuntimeError("Mock mode requires a fixture file on the endpoint")
        path = self.fixtures_dir / fixture_name
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _build_query(
        self,
        endpoint: dict[str, Any],
        *,
        since: str | None,
        page_token: str | None,
        offset: int | None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        for key, value in (endpoint.get("query") or {}).items():
            if isinstance(value, str):
                query[key] = value.replace("{page_size}", str(self._page_size()))
            else:
                query[key] = value

        since_param = endpoint.get("since_param")
        if since and since_param:
            query[str(since_param)] = since

        pagination = endpoint.get("pagination") or {}
        ptype = pagination.get("type", "none")
        if ptype == "page_token" and page_token:
            query[str(pagination.get("token_param", "pageToken"))] = page_token
        if ptype == "offset":
            if offset is not None:
                query[str(pagination.get("offset_param", "offset"))] = offset
            query[str(pagination.get("limit_param", "limit"))] = self._page_size()
        return query

    def _request(
        self,
        endpoint: dict[str, Any],
        *,
        since: str | None = None,
        page_token: str | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        if self.mock:
            return self._load_fixture(endpoint)

        if not self.base_url:
            raise RuntimeError("REDONLINE_BASE_URL is required when not in mock mode")

        method = str(endpoint.get("method", "GET")).upper()
        path = str(endpoint.get("path", "/"))
        url = f"{self.base_url}{path}"
        headers, auth_params = self._auth_headers_and_params()
        query = self._build_query(
            endpoint, since=since, page_token=page_token, offset=offset
        )
        query.update(auth_params)

        logger.debug("%s %s params=%s", method, url, query)
        resp = self._http.request(method, url, headers=headers, params=query)
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object from {url}, got {type(payload)}")
        return payload

    def fetch_all(
        self,
        endpoint_name: str,
        *,
        since: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all pages for a named endpoint and return item dicts."""
        return list(self.iter_items(endpoint_name, since=since))

    def iter_items(
        self,
        endpoint_name: str,
        *,
        since: str | None = None,
    ) -> Iterator[dict[str, Any]]:
        endpoint = self._endpoint(endpoint_name)
        pagination = endpoint.get("pagination") or {}
        ptype = pagination.get("type", "none")
        items_path = endpoint.get("items_path", "data.items")

        page_token: str | None = None
        offset = 0
        seen_tokens: set[str] = set()

        while True:
            payload = self._request(
                endpoint,
                since=since,
                page_token=page_token,
                offset=offset if ptype == "offset" else None,
            )
            items = dig(payload, items_path)
            if items is None:
                items = []
            if not isinstance(items, list):
                raise ValueError(
                    f"items_path '{items_path}' did not resolve to a list "
                    f"for {endpoint_name}"
                )

            for item in items:
                if isinstance(item, dict):
                    yield item
                else:
                    logger.warning(
                        "Skipping non-object item from %s: %r", endpoint_name, item
                    )

            if self.mock:
                break

            if ptype == "none":
                break
            if ptype == "page_token":
                next_token = dig(payload, pagination.get("next_token_path"))
                if not next_token or next_token in seen_tokens:
                    break
                seen_tokens.add(str(next_token))
                page_token = str(next_token)
                continue
            if ptype == "offset":
                if not items:
                    break
                offset += len(items)
                total = dig(payload, pagination.get("total_path"))
                if total is not None and offset >= int(total):
                    break
                continue
            if ptype == "link":
                next_url = dig(payload, pagination.get("next_link_path", "data.next"))
                if not next_url:
                    break
                headers, _ = self._auth_headers_and_params()
                resp = self._http.get(str(next_url), headers=headers)
                resp.raise_for_status()
                payload = resp.json()
                items = dig(payload, items_path) or []
                for item in items:
                    if isinstance(item, dict):
                        yield item
                break

            break
