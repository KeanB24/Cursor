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


def _as_item_list(payload: Any, items_path: str | None) -> list[Any]:
    """Extract a list of items; null/empty path means payload itself may be the list."""
    if items_path:
        items = dig(payload, items_path)
    else:
        items = payload
    if items is None:
        return []
    if isinstance(items, list):
        return items
    if isinstance(items, dict):
        # Single object response — treat as one-item list
        return [items]
    raise ValueError(f"Expected list (or object) at items_path={items_path!r}, got {type(items)}")


def resolve_verify_ssl(value: bool | None = None) -> bool:
    """Resolve TLS verification. False when REDONLINE_VERIFY_SSL is 0/false/no."""
    if value is not None:
        return value
    return os.getenv("REDONLINE_VERIFY_SSL", "1").lower() not in {
        "0",
        "false",
        "no",
    }


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
        verify_ssl: bool | None = None,
    ) -> None:
        self._config = endpoints_config or load_endpoints()
        self.base_url = self._resolve_base_url(base_url)
        self.token = token if token is not None else self._resolve_api_key()
        self.mock = (
            mock
            if mock is not None
            else os.getenv("REDONLINE_MOCK", "0").lower() in {"1", "true", "yes"}
        )
        self.fixtures_dir = fixtures_dir or (project_root() / "fixtures")
        self._owns_http = http_client is None
        self.verify_ssl = resolve_verify_ssl(verify_ssl)
        self._http = http_client or httpx.Client(
            timeout=self._timeout(),
            verify=self.verify_ssl,
        )
        if not self.verify_ssl and self._owns_http:
            logger.warning(
                "TLS certificate verification disabled for Red Online "
                "(REDONLINE_VERIFY_SSL=0 / --insecure)"
            )

    def _resolve_base_url(self, base_url: str | None) -> str:
        if base_url:
            return base_url.rstrip("/")
        env = os.getenv("REDONLINE_BASE_URL")
        if env:
            return env.rstrip("/")
        cfg_url = self._config.get("base_url")
        if cfg_url:
            return str(cfg_url).rstrip("/")
        return ""

    def _resolve_api_key(self) -> str | None:
        for name in ("REDONLINE_API_KEY", "REDONLINE_TOKEN"):
            value = os.getenv(name)
            if value:
                return value
        auth = self._config.get("auth") or {}
        api_key = auth.get("api_key")
        return str(api_key) if api_key else None

    def _timeout(self) -> float:
        defaults = self._config.get("defaults") or {}
        return float(defaults.get("timeout_seconds", 60))

    def _page_size(self) -> int:
        defaults = self._config.get("defaults") or {}
        return int(defaults.get("page_size", 100))

    def _template_vars(self) -> dict[str, str]:
        defaults = self._config.get("defaults") or {}
        return {
            "page_size": str(self._page_size()),
            "site_id": os.getenv("REDONLINE_SITE_ID")
            or str(defaults.get("site_id", "")),
            "user_id": os.getenv("REDONLINE_USER_ID")
            or str(defaults.get("user_id", "")),
        }

    def _render(self, value: str, extra: dict[str, str] | None = None) -> str:
        vars_ = self._template_vars()
        if extra:
            vars_.update(extra)
        out = value
        for key, replacement in vars_.items():
            out = out.replace(f"{{{key}}}", replacement)
        return out

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

    def _load_fixture(self, endpoint: dict[str, Any]) -> Any:
        fixture_name = endpoint.get("fixture")
        if not fixture_name:
            raise RuntimeError("Mock mode requires a fixture file on the endpoint")
        path = self.fixtures_dir / fixture_name
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)

    def _resolve_path(
        self,
        endpoint: dict[str, Any],
        path_vars: dict[str, str] | None = None,
    ) -> str:
        path = str(endpoint.get("path", "/"))
        extra: dict[str, str] = dict(path_vars or {})
        for key, value in (endpoint.get("path_params") or {}).items():
            extra[str(key)] = self._render(str(value), path_vars)
        return self._render(path, extra)

    def _build_query(
        self,
        endpoint: dict[str, Any],
        *,
        since: str | None,
        page_token: str | None,
        offset: int | None,
        path_vars: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        for key, value in (endpoint.get("query") or {}).items():
            if isinstance(value, str):
                query[key] = self._render(value, path_vars)
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
        path_vars: dict[str, str] | None = None,
    ) -> Any:
        if self.mock:
            return self._load_fixture(endpoint)

        if not self.base_url:
            raise RuntimeError("REDONLINE_BASE_URL is required when not in mock mode")

        method = str(endpoint.get("method", "GET")).upper()
        path = self._resolve_path(endpoint, path_vars)
        url = f"{self.base_url}{path}"
        headers, auth_params = self._auth_headers_and_params()
        query = self._build_query(
            endpoint,
            since=since,
            page_token=page_token,
            offset=offset,
            path_vars=path_vars,
        )
        query.update(auth_params)

        logger.debug("%s %s params=%s headers_keys=%s", method, url, query, list(headers))
        resp = self._http.request(method, url, headers=headers, params=query)
        resp.raise_for_status()
        return resp.json()

    def fetch_all(
        self,
        endpoint_name: str,
        *,
        since: str | None = None,
        path_vars: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch all pages for a named endpoint and return item dicts."""
        return list(self.iter_items(endpoint_name, since=since, path_vars=path_vars))

    def iter_items(
        self,
        endpoint_name: str,
        *,
        since: str | None = None,
        path_vars: dict[str, str] | None = None,
    ) -> Iterator[dict[str, Any]]:
        endpoint = self._endpoint(endpoint_name)
        pagination = endpoint.get("pagination") or {}
        ptype = pagination.get("type", "none")
        items_path = endpoint.get("items_path")

        page_token: str | None = None
        offset = 0
        seen_tokens: set[str] = set()

        while True:
            payload = self._request(
                endpoint,
                since=since,
                page_token=page_token,
                offset=offset if ptype == "offset" else None,
                path_vars=path_vars,
            )
            items = _as_item_list(payload, items_path)

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
                for item in _as_item_list(payload, items_path):
                    if isinstance(item, dict):
                        yield item
                break

            break
