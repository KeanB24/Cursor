"""Cognite RAW staging helpers."""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable

from cognite.client import CogniteClient
from cognite.client.data_classes.raw import RowWrite

logger = logging.getLogger(__name__)


def _serialize_columns(columns: dict[str, Any]) -> dict[str, Any]:
    """Ensure RAW column values are JSON-serializable primitives or nested JSON."""
    out: dict[str, Any] = {}
    for key, value in columns.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            out[key] = value
        elif isinstance(value, (dict, list)):
            # Cognite RAW accepts nested JSON; keep structure.
            out[key] = value
        else:
            out[key] = json.dumps(value, default=str)
    return out


class RawStaging:
    """Upsert rows into Cognite RAW tables used as the staging area."""

    def __init__(self, client: CogniteClient, database: str) -> None:
        self.client = client
        self.database = database

    def ensure_table(self, table: str) -> None:
        self.client.raw.rows.insert(
            db_name=self.database,
            table_name=table,
            row=RowWrite(key="__bootstrap__", columns={"_init": True}),
            ensure_parent=True,
        )
        # Remove bootstrap marker if present (best-effort)
        try:
            self.client.raw.rows.delete(self.database, table, ["__bootstrap__"])
        except Exception:  # noqa: BLE001 — cleanup is best-effort
            logger.debug("Bootstrap row cleanup skipped for %s/%s", self.database, table)

    def upsert_rows(
        self,
        table: str,
        rows: Iterable[dict[str, Any]],
        *,
        id_field: str = "id",
        batch_size: int = 10000,
        ensure_parent: bool = True,
        extra_columns: dict[str, Any] | None = None,
    ) -> int:
        """
        Upsert dict rows into RAW. Returns count of rows written.

        Each row must contain `id_field` used as the RAW row key.
        """
        buffer: list[RowWrite] = []
        total = 0

        def flush() -> None:
            nonlocal total, buffer
            if not buffer:
                return
            self.client.raw.rows.insert(
                db_name=self.database,
                table_name=table,
                row=buffer,
                ensure_parent=ensure_parent,
            )
            total += len(buffer)
            buffer = []

        for record in rows:
            key = record.get("_raw_key", record.get(id_field))
            if key is None:
                logger.warning(
                    "Skipping row without _raw_key/%s in table %s", id_field, table
                )
                continue
            columns = {k: v for k, v in record.items() if k != "_raw_key"}
            if extra_columns:
                columns.update(extra_columns)
            buffer.append(
                RowWrite(key=str(key), columns=_serialize_columns(columns))
            )
            if len(buffer) >= batch_size:
                flush()

        flush()
        logger.info("Upserted %s rows into RAW %s/%s", total, self.database, table)
        return total

    def list_rows(self, table: str, limit: int | None = None) -> list[dict[str, Any]]:
        """Read RAW rows back as dicts (includes row key as `_key`)."""
        result: list[dict[str, Any]] = []
        for row in self.client.raw.rows(
            db_name=self.database,
            table_name=table,
            limit=limit if limit is not None else -1,
        ):
            cols = dict(row.columns or {})
            cols["_key"] = row.key
            result.append(cols)
        return result
