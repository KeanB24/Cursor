"""Load staged rows into existing Cognite Data Model views."""

from __future__ import annotations

import logging
from typing import Any

from cognite.client import CogniteClient
from cognite.client.data_classes.data_modeling import (
    NodeApply,
    NodeOrEdgeData,
    ViewId,
)

logger = logging.getLogger(__name__)


def map_row_to_properties(
    row: dict[str, Any],
    field_map: dict[str, Any],
    *,
    constants: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Map a RAW/source row to (external_id, properties) using field_maps.yaml entry.

    `field_map` shape:
      externalId: <source field>
      properties:
        dmProp: sourceField
    """
    merged = dict(row)
    if constants:
        for key, value in constants.items():
            merged.setdefault(key, value)

    id_source = field_map.get("externalId", "id")
    external_id = merged.get(id_source)
    if external_id is None:
        raise ValueError(f"Row missing external id field '{id_source}': {row!r}")

    props: dict[str, Any] = {}
    for dm_prop, source_field in (field_map.get("properties") or {}).items():
        if source_field in merged and merged[source_field] is not None:
            props[dm_prop] = merged[source_field]
    return str(external_id), props


class DataModelLoader:
    """Upsert nodes into existing Action Item Management views."""

    def __init__(
        self,
        client: CogniteClient,
        *,
        instance_space: str,
        views: dict[str, dict[str, str]],
        field_maps: dict[str, Any],
    ) -> None:
        self.client = client
        self.instance_space = instance_space
        self.views = views
        self.field_maps = field_maps
        self.constants = field_maps.get("constants") or {}

    def _view_id(self, view_key: str) -> ViewId:
        cfg = self.views[view_key]
        return ViewId(
            space=cfg["space"],
            external_id=cfg["external_id"],
            version=str(cfg["version"]),
        )

    def build_nodes(
        self,
        view_key: str,
        rows: list[dict[str, Any]],
    ) -> list[NodeApply]:
        field_map = self.field_maps[view_key]
        view_id = self._view_id(view_key)
        nodes: list[NodeApply] = []
        for row in rows:
            try:
                external_id, props = map_row_to_properties(
                    row, field_map, constants=self.constants
                )
            except ValueError as exc:
                logger.warning("Skipping row: %s", exc)
                continue
            nodes.append(
                NodeApply(
                    space=self.instance_space,
                    external_id=external_id,
                    sources=[
                        NodeOrEdgeData(source=view_id, properties=props),
                    ],
                )
            )
        return nodes

    def apply_nodes(
        self,
        view_key: str,
        rows: list[dict[str, Any]],
        *,
        batch_size: int = 1000,
        replace: bool = False,
    ) -> int:
        nodes = self.build_nodes(view_key, rows)
        if not nodes:
            return 0
        total = 0
        for i in range(0, len(nodes), batch_size):
            chunk = nodes[i : i + batch_size]
            self.client.data_modeling.instances.apply(nodes=chunk, replace=replace)
            total += len(chunk)
        logger.info(
            "Applied %s nodes for view_key=%s space=%s",
            total,
            view_key,
            self.instance_space,
        )
        return total
