"""Orchestrate extract → RAW stage → data model load."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from cognite.client import CogniteClient

from redonline_cdf.cognite.dm_loader import DataModelLoader
from redonline_cdf.cognite.raw_staging import RawStaging
from redonline_cdf.config import load_field_maps, load_settings
from redonline_cdf.models import coerce_record
from redonline_cdf.pipeline.state import IngestionState, max_watermark
from redonline_cdf.redonline import RedOnlineClient

logger = logging.getLogger(__name__)


@dataclass
class EntityResult:
    name: str
    extracted: int = 0
    staged: int = 0
    loaded: int = 0
    watermark: str | None = None


@dataclass
class IngestResult:
    entities: list[EntityResult] = field(default_factory=list)
    dry_run: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "entities": [
                {
                    "name": e.name,
                    "extracted": e.extracted,
                    "staged": e.staged,
                    "loaded": e.loaded,
                    "watermark": e.watermark,
                }
                for e in self.entities
            ],
        }


class IngestPipeline:
    """Full Red Online → Cognite RAW → DM ingest run."""

    def __init__(
        self,
        *,
        cognite: CogniteClient | None,
        redonline: RedOnlineClient,
        settings: dict[str, Any] | None = None,
        field_maps: dict[str, Any] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.cognite = cognite
        self.redonline = redonline
        self.settings = settings or load_settings()
        self.field_maps = field_maps or load_field_maps()
        self.dry_run = dry_run

    def run(self, entities: list[str] | None = None) -> IngestResult:
        result = IngestResult(dry_run=self.dry_run)
        raw_cfg = self.settings["raw"]
        database = raw_cfg["database"]
        tables = raw_cfg["tables"]
        batch = self.settings.get("batch") or {}
        dm_cfg = self.settings["data_model"]

        staging: RawStaging | None = None
        state: IngestionState | None = None
        loader: DataModelLoader | None = None

        if not self.dry_run:
            if self.cognite is None:
                raise RuntimeError("Cognite client is required unless dry_run=True")
            staging = RawStaging(self.cognite, database)
            state = IngestionState(
                self.cognite,
                database=database,
                table=tables["ingestion_state"],
            )
            loader = DataModelLoader(
                self.cognite,
                instance_space=dm_cfg["instance_space"],
                views=dm_cfg["views"],
                field_maps=self.field_maps,
            )

        entity_defs = self.settings.get("entities") or []
        for entity in entity_defs:
            name = entity["name"]
            if entities and name not in entities:
                continue
            er = self._run_entity(
                entity,
                tables=tables,
                staging=staging,
                state=state,
                loader=loader,
                batch=batch,
            )
            result.entities.append(er)

        return result

    def _run_entity(
        self,
        entity: dict[str, Any],
        *,
        tables: dict[str, str],
        staging: RawStaging | None,
        state: IngestionState | None,
        loader: DataModelLoader | None,
        batch: dict[str, Any],
    ) -> EntityResult:
        name = entity["name"]
        endpoint = entity["endpoint"]
        raw_table_key = entity["raw_table"]
        raw_table = tables[raw_table_key]
        view_key = entity["view_key"]
        id_field = entity.get("id_field", "id")
        watermark_field = entity.get("watermark_field", "updatedAt")

        since = state.get_watermark(name) if state else None
        logger.info("Extracting %s (since=%s)", name, since)

        records = [
            coerce_record(item)
            for item in self.redonline.fetch_all(endpoint, since=since)
        ]
        er = EntityResult(name=name, extracted=len(records))

        if self.dry_run:
            er.staged = len(records)
            er.loaded = len(records)
            er.watermark = max_watermark(records, watermark_field) or since
            logger.info(
                "[dry-run] %s extracted=%s would stage/load to %s / view=%s",
                name,
                er.extracted,
                raw_table,
                view_key,
            )
            return er

        assert staging is not None and loader is not None
        constants = self.field_maps.get("constants") or {}
        er.staged = staging.upsert_rows(
            raw_table,
            records,
            id_field=id_field,
            batch_size=int(batch.get("raw_upsert_size", 10000)),
            extra_columns=constants,
        )

        enriched = [{**r, **constants} for r in records]
        er.loaded = loader.apply_nodes(
            view_key,
            enriched,
            batch_size=int(batch.get("dm_apply_size", 1000)),
        )

        new_wm = max_watermark(records, watermark_field)
        if new_wm and state is not None:
            state.set_watermark(
                name,
                new_wm,
                extra={
                    "extracted": er.extracted,
                    "staged": er.staged,
                    "loaded": er.loaded,
                },
            )
            er.watermark = new_wm
        else:
            er.watermark = since

        return er


def run_ingest(
    *,
    cognite: CogniteClient | None,
    redonline: RedOnlineClient,
    dry_run: bool = False,
    entities: list[str] | None = None,
) -> dict[str, Any]:
    pipeline = IngestPipeline(
        cognite=cognite,
        redonline=redonline,
        dry_run=dry_run,
    )
    return pipeline.run(entities=entities).as_dict()
