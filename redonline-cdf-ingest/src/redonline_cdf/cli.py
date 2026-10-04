"""Console script and shared CLI for local / VM runs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_paths() -> None:
    root = _project_root()
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    os.environ.setdefault("CONFIG_DIR", str(root / "config"))


def _load_project_dotenv(root: Path) -> None:
    """Load root/.env so CLI matches discover_rol_schema.py behavior."""
    env_path = root / ".env"
    try:
        from dotenv import load_dotenv

        # utf-8-sig strips a Windows BOM that would otherwise break key names
        load_dotenv(env_path, encoding="utf-8-sig")
        return
    except TypeError:
        # Older python-dotenv without encoding= support
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
            return
        except ImportError:
            pass
    except ImportError:
        pass

    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main(argv: list[str] | None = None) -> int:
    _ensure_paths()
    root = _project_root()
    _load_project_dotenv(root)

    parser = argparse.ArgumentParser(
        description="Ingest Red Online EHS data into Cognite Action Item Management"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use fixtures/ instead of calling Red Online",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and map only; skip Cognite RAW/DM writes",
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (corporate SSL interception)",
    )
    parser.add_argument(
        "--entities",
        nargs="*",
        default=None,
        help="Optional subset of entity names (sites users tasks references)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
    )
    args = parser.parse_args(argv)

    if args.insecure:
        os.environ["REDONLINE_VERIFY_SSL"] = "0"

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    log = logging.getLogger("redonline_cdf.cli")

    from redonline_cdf.auth import create_cognite_client, resolve_redonline_token
    from redonline_cdf.pipeline import run_ingest
    from redonline_cdf.redonline import RedOnlineClient
    from redonline_cdf.redonline.client import resolve_verify_ssl

    mock = args.mock or os.getenv("REDONLINE_MOCK", "0").lower() in {"1", "true", "yes"}
    verify_ssl = resolve_verify_ssl()
    token = None if mock else resolve_redonline_token()

    log.info(
        "Starting ingest mock=%s dry_run=%s tls_verify=%s env=%s",
        mock,
        args.dry_run,
        verify_ssl,
        root / ".env",
    )

    cognite = None
    if not args.dry_run:
        try:
            cognite = create_cognite_client()
        except RuntimeError as exc:
            log.error("%s", exc)
            return 1
        log.info(
            "Cognite client ready project=%s cluster=%s",
            os.getenv("CDF_PROJECT"),
            os.getenv("CDF_CLUSTER", "az-eastus-1"),
        )

    with RedOnlineClient(token=token, mock=mock, verify_ssl=verify_ssl) as red:
        result = run_ingest(
            cognite=cognite,
            redonline=red,
            dry_run=args.dry_run,
            entities=args.entities,
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
