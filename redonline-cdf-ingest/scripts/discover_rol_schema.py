#!/usr/bin/env python
"""
Call live ROL / HSE APIs and save responses for RAW table design.

Writes under samples/rol/:
  - <endpoint>_raw.json      full API response
  - <endpoint>_items.json    extracted item list (best effort)
  - schema_summary.json      inferred fields per endpoint
  - schema_summary.md        human-readable field catalog

Usage:
  python scripts/discover_rol_schema.py
  python scripts/discover_rol_schema.py --endpoints list_sites list_tasks_by_user
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CONFIG_DIR", str(ROOT / "config"))


def _ensure_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass


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


def _walk_fields(
    obj: Any,
    prefix: str = "",
    out: dict[str, set[str]] | None = None,
) -> dict[str, set[str]]:
    """Collect dotted field paths and observed types from sample objects."""
    if out is None:
        out = defaultdict(set)
    if isinstance(obj, dict):
        if not obj and prefix:
            out[prefix].add("object")
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out[path].add(_infer_type(value))
            if isinstance(value, dict):
                _walk_fields(value, path, out)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                _walk_fields(value[0], f"{path}[]", out)
    return out


def _guess_id_field(fields: dict[str, set[str]]) -> str | None:
    candidates = [
        "id",
        "Id",
        "ID",
        "externalId",
        "external_id",
        "task_id",
        "taskId",
        "user_id",
        "userId",
        "site_id",
        "siteId",
    ]
    top_level = [f for f in fields if "." not in f and "[]" not in f]
    for name in candidates:
        if name in top_level:
            return name
    return top_level[0] if top_level else None


def _detect_items_path(payload: Any) -> str | None:
    """Suggest items_path for endpoints.yaml from a live payload."""
    if isinstance(payload, list):
        return None  # root list
    if not isinstance(payload, dict):
        return None
    for path in ("data.items", "items", "data", "results", "value"):
        from redonline_cdf.redonline.client import dig

        node = dig(payload, path)
        if isinstance(node, list):
            return path
    # first list-valued key at top level
    for key, value in payload.items():
        if isinstance(value, list):
            return key
    return None


def main(argv: list[str] | None = None) -> int:
    _ensure_dotenv()

    parser = argparse.ArgumentParser(
        description="Discover ROL API response shapes for Cognite RAW design"
    )
    parser.add_argument(
        "--endpoints",
        nargs="*",
        default=None,
        help="Endpoint names from endpoints.yaml (default: all)",
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "samples" / "rol"),
        help="Output directory for saved responses",
    )
    args = parser.parse_args(argv)

    from redonline_cdf.auth import resolve_redonline_token
    from redonline_cdf.config import load_endpoints
    from redonline_cdf.redonline.client import RedOnlineClient, dig
    from redonline_cdf.redonline.client import _as_item_list  # type: ignore

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = load_endpoints()
    endpoint_names = args.endpoints or list((cfg.get("endpoints") or {}).keys())

    token = resolve_redonline_token()
    summary: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": os.getenv("REDONLINE_BASE_URL")
        or cfg.get("base_url")
        or "https://apigw.ct-test.hse-compliance.net",
        "endpoints": {},
    }

    md_lines = [
        "# ROL API schema discovery",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "Use this to set `items_path` in `config/endpoints.yaml` and RAW columns / `field_maps.yaml`.",
        "",
    ]

    with RedOnlineClient(token=token, mock=False) as client:
        for name in endpoint_names:
            print(f"Calling {name}...")
            endpoint = client._endpoint(name)
            try:
                payload = client._request(endpoint)
            except Exception as exc:  # noqa: BLE001 — discovery should continue
                print(f"  FAILED: {type(exc).__name__}: {exc}")
                summary["endpoints"][name] = {"error": str(exc)}
                md_lines.extend([f"## `{name}`", "", f"**Error:** `{exc}`", ""])
                continue

            raw_path = out_dir / f"{name}_raw.json"
            raw_path.write_text(
                json.dumps(payload, indent=2, default=str), encoding="utf-8"
            )

            suggested_items_path = _detect_items_path(payload)
            items_path = endpoint.get("items_path")
            if items_path is None and suggested_items_path is not None:
                # Prefer detected path when config says null but response is wrapped
                try_path = suggested_items_path
            else:
                try_path = items_path

            try:
                items = _as_item_list(payload, try_path)
            except ValueError:
                items = []
                if isinstance(payload, dict):
                    items = [payload]

            items_path_file = out_dir / f"{name}_items.json"
            items_path_file.write_text(
                json.dumps(items, indent=2, default=str), encoding="utf-8"
            )

            field_types: dict[str, set[str]] = defaultdict(set)
            for item in items[:50]:
                if isinstance(item, dict):
                    _walk_fields(item, "", field_types)

            fields = {
                path: sorted(types) for path, types in sorted(field_types.items())
            }
            id_field = _guess_id_field(field_types)

            entry = {
                "raw_file": str(raw_path.relative_to(ROOT)),
                "items_file": str(items_path_file.relative_to(ROOT)),
                "item_count": len(items),
                "configured_items_path": items_path,
                "suggested_items_path": suggested_items_path,
                "suggested_id_field": id_field,
                "fields": fields,
                "sample_item": items[0] if items else None,
            }
            summary["endpoints"][name] = entry

            print(
                f"  saved {raw_path.name} ({len(items)} items); "
                f"suggested items_path={suggested_items_path!r}; id={id_field!r}"
            )

            md_lines.extend(
                [
                    f"## `{name}`",
                    "",
                    f"- Raw: `{entry['raw_file']}`",
                    f"- Items: `{entry['items_file']}` ({len(items)} rows)",
                    f"- Configured `items_path`: `{items_path}`",
                    f"- Suggested `items_path`: `{suggested_items_path}`",
                    f"- Suggested RAW row key: `{id_field}`",
                    "",
                    "| Field | Observed types |",
                    "|-------|----------------|",
                ]
            )
            for path, types in fields.items():
                md_lines.append(f"| `{path}` | {', '.join(types)} |")
            md_lines.append("")

    summary_json = out_dir / "schema_summary.json"
    summary_md = out_dir / "schema_summary.md"
    summary_json.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    summary_md.write_text("\n".join(md_lines), encoding="utf-8")

    print()
    print(f"Wrote {summary_json}")
    print(f"Wrote {summary_md}")
    print()
    print("Next:")
    print("  1. Open samples/rol/*_raw.json and confirm the response shape")
    print("  2. Set items_path / id_field in config/endpoints.yaml and settings.yaml")
    print("  3. Map fields in config/field_maps.yaml from schema_summary.md")
    print("  4. Re-run: python scripts/run_local.py --dry-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
