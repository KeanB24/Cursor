"""Cognite Function entrypoint."""

from __future__ import annotations

import logging
import os
from typing import Any

from redonline_cdf.auth import resolve_redonline_token
from redonline_cdf.pipeline import run_ingest
from redonline_cdf.redonline import RedOnlineClient

logger = logging.getLogger(__name__)


def handle(data: dict[str, Any] | None = None, client: Any = None) -> dict[str, Any]:
    """
    Cognite Function handler.

    Parameters
    ----------
    data:
        Optional payload from the Function call / schedule. Supported keys:
        - dry_run (bool)
        - mock (bool)
        - entities (list[str]) — subset of entity names to ingest
    client:
        CogniteClient injected by the Cognite Functions runtime.
    """
    data = data or {}
    dry_run = bool(data.get("dry_run", False))
    mock = bool(data.get("mock", os.getenv("REDONLINE_MOCK", "0") in {"1", "true", "yes"}))
    entities = data.get("entities")

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    token = None if mock else resolve_redonline_token()
    with RedOnlineClient(token=token, mock=mock) as red:
        result = run_ingest(
            cognite=client,
            redonline=red,
            dry_run=dry_run,
            entities=entities,
        )
    logger.info("Ingest complete: %s", result)
    return result
