#!/usr/bin/env python
"""
Standalone ROL / HSE API discovery — no package imports.

Calls each endpoint, saves JSON under samples/rol/, and prints field hints
for Cognite RAW design.

Usage (from redonline-cdf-ingest folder):
  python scripts/discover_rol_schema.py
  python scripts/discover_rol_schema.py --insecure
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "endpoints.yaml"
OUT_DIR = ROOT / "samples" / "rol"


def _load_dotenv() -> None:
    """Load project `.env`, then parent workspace `.env` (first wins per key)."""
    for env_path in (ROOT / ".env", ROOT.parent / ".env"):
        if not env_path.is_file():
            continue
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise SystemExit(
            "PyYAML is required. Run: python -m pip install PyYAML"
        ) from exc
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"Expected mapping in {path}")
    return data


def _dig(data: Any, path: str | None) -> Any:
    if not path:
        return data
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _as_items(payload: Any, items_path: str | None) -> list[Any]:
    node = _dig(payload, items_path) if items_path else payload
    if node is None:
        return []
    if isinstance(node, list):
        return node
    if isinstance(node, dict):
        return [node]
    return []


def _infer_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _walk_fields(obj: Any, prefix: str = "", out: dict[str, set[str]] | None = None):
    if out is None:
        out = defaultdict(set)
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out[path].add(_infer_type(value))
            if isinstance(value, dict):
                _walk_fields(value, path, out)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                _walk_fields(value[0], f"{path}[]", out)
    return out


def _guess_id_field(fields: dict[str, set[str]]) -> str | None:
    candidates = ["id", "Id", "ID", "externalId", "taskId", "userId", "siteId"]
    top = [f for f in fields if "." not in f and "[]" not in f]
    for name in candidates:
        if name in top:
            return name
    return top[0] if top else None


def _detect_items_path(payload: Any) -> str | None:
    if isinstance(payload, list):
        return None
    if not isinstance(payload, dict):
        return None
    for path in ("data.items", "items", "data", "results", "value"):
        if isinstance(_dig(payload, path), list):
            return path
    for key, value in payload.items():
        if isinstance(value, list):
            return key
    return None


def _render(template: str, vars_: dict[str, str]) -> str:
    out = template
    for key, value in vars_.items():
        out = out.replace(f"{{{key}}}", value)
    return out


def _http_get(
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
    *,
    insecure: bool,
    timeout: float,
) -> Any:
    if params:
        url = f"{url}?{urlencode({k: str(v) for k, v in params.items()})}"
    req = Request(url, headers=headers, method="GET")
    context = ssl._create_unverified_context() if insecure else None
    try:
        with urlopen(req, timeout=timeout, context=context) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else None
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} for {url}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"Connection failed for {url}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()

    parser = argparse.ArgumentParser(description="Discover ROL API response shapes")
    parser.add_argument("--endpoints", nargs="*", default=None)
    parser.add_argument("--out", default=str(OUT_DIR))
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (corporate SSL interception)",
    )
    args = parser.parse_args(argv)

    insecure = args.insecure or os.getenv("REDONLINE_VERIFY_SSL", "1").lower() in {
        "0",
        "false",
        "no",
    }

    if not CONFIG_PATH.exists():
        print(f"ERROR: config not found: {CONFIG_PATH}")
        print("Run this script from the redonline-cdf-ingest project, or keep config/ next to scripts/.")
        return 1

    cfg = _load_yaml(CONFIG_PATH)
    base_url = (
        os.getenv("REDONLINE_BASE_URL")
        or str(cfg.get("base_url") or "")
    ).rstrip("/")
    auth = cfg.get("auth") or {}
    api_key = (
        os.getenv("REDONLINE_API_KEY")
        or os.getenv("REDONLINE_TOKEN")
        or auth.get("api_key")
        or ""
    )
    defaults = cfg.get("defaults") or {}
    site_id = os.getenv("REDONLINE_SITE_ID") or str(defaults.get("site_id", "112087"))
    user_id = os.getenv("REDONLINE_USER_ID") or str(defaults.get("user_id", "584646"))
    timeout = float(defaults.get("timeout_seconds", 60))
    vars_ = {"site_id": site_id, "user_id": user_id, "page_size": "100"}

    print("=== ROL discovery ===")
    print(f"project root : {ROOT}")
    print(f"config       : {CONFIG_PATH}")
    print(f"base_url     : {base_url or '(MISSING)'}")
    print(f"api_key set  : {bool(api_key)} (header {auth.get('header_name', 'X-ROL-API-KEY')})")
    print(f"site_id      : {site_id}")
    print(f"user_id      : {user_id}")
    print(f"tls verify   : {not insecure}")
    print()

    if not base_url:
        print("ERROR: base_url missing. Set REDONLINE_BASE_URL or config/endpoints.yaml base_url.")
        return 1
    if not api_key:
        print("ERROR: API key missing. Set REDONLINE_API_KEY or auth.api_key in endpoints.yaml.")
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    endpoints = cfg.get("endpoints") or {}
    names = args.endpoints or list(endpoints.keys())
    header_name = str(auth.get("header_name") or "X-ROL-API-KEY")

    summary: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "insecure_tls": insecure,
        "endpoints": {},
    }
    md = [
        "# ROL API schema discovery",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Base URL: `{base_url}`",
        f"TLS verify: `{not insecure}`",
        "",
    ]

    for name in names:
        ep = endpoints.get(name)
        if not ep:
            print(f"SKIP unknown endpoint: {name}")
            continue

        path = _render(str(ep.get("path", "/")), vars_)
        for key, value in (ep.get("path_params") or {}).items():
            path = path.replace(f"{{{key}}}", _render(str(value), vars_))

        query: dict[str, Any] = {}
        for key, value in (ep.get("query") or {}).items():
            query[key] = _render(str(value), vars_) if isinstance(value, str) else value

        url = f"{base_url}{path}"
        headers = {"Accept": "application/json", header_name: api_key}

        print(f"GET {url} params={query}")
        try:
            payload = _http_get(url, headers, query, insecure=insecure, timeout=timeout)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            if "CERTIFICATE" in str(exc).upper() or "SSL" in str(exc).upper():
                print("  Hint: re-run with --insecure  (corporate SSL interception)")
            summary["endpoints"][name] = {"error": str(exc), "url": url}
            md.extend([f"## `{name}`", "", f"**Error:** `{exc}`", ""])
            continue

        raw_path = out_dir / f"{name}_raw.json"
        raw_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

        suggested = _detect_items_path(payload)
        items_path = ep.get("items_path")
        try_path = suggested if items_path is None and suggested is not None else items_path
        items = _as_items(payload, try_path)

        items_file = out_dir / f"{name}_items.json"
        items_file.write_text(json.dumps(items, indent=2, default=str), encoding="utf-8")

        field_types: dict[str, set[str]] = defaultdict(set)
        for item in items[:50]:
            if isinstance(item, dict):
                _walk_fields(item, "", field_types)
        fields = {p: sorted(t) for p, t in sorted(field_types.items())}
        id_field = _guess_id_field(field_types)

        summary["endpoints"][name] = {
            "url": url,
            "raw_file": str(raw_path.relative_to(ROOT)),
            "items_file": str(items_file.relative_to(ROOT)),
            "item_count": len(items),
            "suggested_items_path": suggested,
            "suggested_id_field": id_field,
            "fields": fields,
            "sample_item": items[0] if items else None,
        }
        print(
            f"  OK -> {raw_path.name} | items={len(items)} | "
            f"items_path={suggested!r} | id={id_field!r}"
        )

        md.extend(
            [
                f"## `{name}`",
                "",
                f"- URL: `{url}`",
                f"- Raw: `{raw_path.relative_to(ROOT)}`",
                f"- Items: {len(items)}",
                f"- Suggested items_path: `{suggested}`",
                f"- Suggested id field: `{id_field}`",
                "",
                "| Field | Types |",
                "|-------|-------|",
            ]
        )
        for path_name, types in fields.items():
            md.append(f"| `{path_name}` | {', '.join(types)} |")
        md.append("")

    (out_dir / "schema_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8"
    )
    (out_dir / "schema_summary.md").write_text("\n".join(md), encoding="utf-8")
    print()
    print(f"Wrote {out_dir / 'schema_summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
