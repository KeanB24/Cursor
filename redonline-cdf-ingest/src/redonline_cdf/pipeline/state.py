"""Watermark / run-state persistence in Cognite RAW."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from cognite.client import CogniteClient
from cognite.client.data_classes.raw import RowWrite
from cognite.client.exceptions import CogniteAPIError

logger = logging.getLogger(__name__)


class IngestionState:
    """Store per-entity watermarks in a RAW table."""

    def __init__(
        self,
        client: CogniteClient,
        *,
        database: str,
        table: str = "ingestion_state",
    ) -> None:
        self.client = client
        self.database = database
        self.table = table

    def get_watermark(self, entity: str) -> str | None:
        try:
            row = self.client.raw.rows.retrieve(self.database, self.table, entity)
        except CogniteAPIError as exc:
            if getattr(exc, "code", None) == 404:
                return None
            logger.debug("Watermark retrieve failed for %s: %s", entity, exc)
            return None
        if row is None:
            return None
        columns = row.columns or {}
        value = columns.get("watermark")
        return str(value) if value is not None else None

    def set_watermark(
        self,
        entity: str,
        watermark: str,
        *,
        extra: dict[str, Any] | None = None,
    ) -> None:
        columns: dict[str, Any] = {
            "watermark": watermark,
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "entity": entity,
        }
        if extra:
            columns.update(extra)
        self.client.raw.rows.insert(
            db_name=self.database,
            table_name=self.table,
            row=RowWrite(key=entity, columns=columns),
            ensure_parent=True,
        )
        logger.info("Saved watermark for %s: %s", entity, watermark)


def max_watermark(rows: list[dict[str, Any]], field: str) -> str | None:
    """Return the lexicographically max timestamp-like value from rows."""
    values = [str(r[field]) for r in rows if r.get(field)]
    if not values:
        return None
    return max(values)
