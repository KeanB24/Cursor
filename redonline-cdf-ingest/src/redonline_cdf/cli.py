"""Console script and shared CLI for local / VM runs."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path


def _ensure_paths() -> None:
    root = Path(__file__).resolve().parents[2]
    src = root / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    os.environ.setdefault("CONFIG_DIR", str(root / "config"))


def main(argv: list[str] | None = None) -> int:
    _ensure_paths()

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

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

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    from redonline_cdf.auth import create_cognite_client, resolve_redonline_token
    from redonline_cdf.pipeline import run_ingest
    from redonline_cdf.redonline import RedOnlineClient

    mock = args.mock or os.getenv("REDONLINE_MOCK", "0").lower() in {"1", "true", "yes"}
    token = None if mock else resolve_redonline_token()

    cognite = None
    if not args.dry_run:
        cognite = create_cognite_client()

    with RedOnlineClient(token=token, mock=mock) as red:
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
