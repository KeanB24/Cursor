"""Orchestrate extract → flatten → Cognite RAW (+ optional DM load)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from cognite.client import CogniteClient

from redonline_cdf.cognite.dm_loader import DataModelLoader
from redonline_cdf.cognite.raw_staging import RawStaging
from redonline_cdf.config import load_field_maps, load_settings
from redonline_cdf.models import coerce_record
from redonline_cdf.pipeline.flatten import transform
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
    tables: dict[str, int] = field(default_factory=dict)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class IngestResult:
    entities: list[EntityResult] = field(default_factory=list)
    dry_run: bool = False
    database: str | None = None
    mode: str = "cascaded"

    def as_dict(self) -> dict[str, Any]:
        return {
            "dry_run": self.dry_run,
            "database": self.database,
            "mode": self.mode,
            "entities": [
                {
                    "name": e.name,
                    "extracted": e.extracted,
                    "staged": e.staged,
                    "loaded": e.loaded,
                    "watermark": e.watermark,
                    "tables": e.tables,
                    "details": e.details,
                }
                for e in self.entities
            ],
        }


def _dedupe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in rows:
        key = str(row.get("_raw_key", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _merge_table_maps(
    *maps: dict[str, list[dict[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    merged: dict[str, list[dict[str, Any]]] = {}
    for m in maps:
        for table, rows in m.items():
            merged.setdefault(table, []).extend(rows)
    return {k: _dedupe_rows(v) for k, v in merged.items()}


class IngestPipeline:
    """Red Online cascaded ingest → Cognite RAW (ROL-COR)."""

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
        """
        Cascaded first-wave ingest:
          1) fetch all sites
          2) for each site → fetch users
          3) for each user → fetch tasks
          4) fetch mapping references once (using first discovered user)
        """
        raw_cfg = self.settings["raw"]
        database = raw_cfg["database"]
        tables = raw_cfg["tables"]
        batch = self.settings.get("batch") or {}
        cascaded = self.settings.get("cascaded") or {}
        load_dm = bool(self.settings.get("load_to_data_model", False))
        result = IngestResult(
            dry_run=self.dry_run,
            database=database,
            mode="cascaded",
        )

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
                table=tables.get("Ingestion_state", "Ingestion_state"),
            )
            if load_dm:
                dm_cfg = self.settings["data_model"]
                loader = DataModelLoader(
                    self.cognite,
                    instance_space=dm_cfg["instance_space"],
                    views=dm_cfg["views"],
                    field_maps=self.field_maps,
                )

        want = set(entities) if entities else None

        # ---- 1) Sites ----
        logger.info("Cascaded ingest: fetching sites")
        site_records = [
            coerce_record(i) for i in self.redonline.fetch_all("list_sites")
        ]
        max_sites = cascaded.get("max_sites")
        if max_sites is not None:
            site_records = site_records[: int(max_sites)]

        site_rows = transform("sites", site_records)
        if want is None or "sites" in want:
            result.entities.append(
                self._stage_bundle(
                    name="sites",
                    extracted=len(site_records),
                    table_rows=site_rows,
                    tables=tables,
                    staging=staging,
                    batch=batch,
                    load_dm=load_dm,
                    loader=loader,
                    state=state,
                    watermark_field=None,
                    records=site_records,
                    details={"sites": len(site_records)},
                )
            )

        # ---- 2) Users per site ----
        all_user_maps: list[dict[str, list[dict[str, Any]]]] = []
        users_seen: set[str] = set()
        user_site_pairs: list[tuple[str, str]] = []
        max_users = cascaded.get("max_users_per_site")
        sites_queried = 0
        users_extracted = 0

        for site in site_records:
            site_id = site.get("id_site")
            if site_id is None:
                continue
            site_id_s = str(site_id)
            sites_queried += 1
            logger.info("Fetching users for site_id=%s", site_id_s)
            try:
                user_records = [
                    coerce_record(i)
                    for i in self.redonline.fetch_all(
                        "list_users_by_site",
                        path_vars={"site_id": site_id_s},
                    )
                ]
            except Exception as exc:  # noqa: BLE001
                logger.warning("Users fetch failed for site %s: %s", site_id_s, exc)
                continue
            if max_users is not None:
                user_records = user_records[: int(max_users)]
            users_extracted += len(user_records)
            all_user_maps.append(transform("users", user_records, site_id=site_id_s))
            for u in user_records:
                uid = u.get("id_user")
                if uid is None:
                    continue
                uid_s = str(uid)
                user_site_pairs.append((uid_s, site_id_s))
                users_seen.add(uid_s)

        user_rows = _merge_table_maps(*all_user_maps) if all_user_maps else {
            "Users": [],
            "User_profiles": [],
        }
        if want is None or "users" in want:
            result.entities.append(
                self._stage_bundle(
                    name="users",
                    extracted=users_extracted,
                    table_rows=user_rows,
                    tables=tables,
                    staging=staging,
                    batch=batch,
                    load_dm=load_dm,
                    loader=loader,
                    state=state,
                    watermark_field=None,
                    records=[],
                    details={
                        "sites_queried": sites_queried,
                        "unique_users": len(users_seen),
                    },
                )
            )

        # ---- 3) Tasks per user ----
        all_task_maps: list[dict[str, list[dict[str, Any]]]] = []
        tasks_extracted = 0
        users_queried = 0
        max_task_users = cascaded.get("max_users_for_tasks")
        unique_users = sorted(users_seen)
        if max_task_users is not None:
            unique_users = unique_users[: int(max_task_users)]

        for user_id in unique_users:
            users_queried += 1
            logger.info("Fetching tasks for user_id=%s", user_id)
            try:
                task_records = [
                    coerce_record(i)
                    for i in self.redonline.fetch_all(
                        "list_tasks_by_user",
                        path_vars={"user_id": user_id},
                    )
                ]
            except Exception as exc:  # noqa: BLE001
                logger.warning("Tasks fetch failed for user %s: %s", user_id, exc)
                continue
            tasks_extracted += len(task_records)
            all_task_maps.append(transform("tasks", task_records, user_id=user_id))

        task_rows = _merge_table_maps(*all_task_maps) if all_task_maps else {
            "Tasks": [],
            "Task_instances": [],
            "Task_occurrences": [],
        }
        if want is None or "tasks" in want:
            result.entities.append(
                self._stage_bundle(
                    name="tasks",
                    extracted=tasks_extracted,
                    table_rows=task_rows,
                    tables=tables,
                    staging=staging,
                    batch=batch,
                    load_dm=load_dm,
                    loader=loader,
                    state=state,
                    watermark_field="updated_at",
                    records=[
                        r
                        for m in all_task_maps
                        for r in m.get("Tasks", [])
                    ],
                    details={
                        "users_queried": users_queried,
                        "unique_tasks": len(task_rows.get("Tasks", [])),
                    },
                )
            )

        # ---- 4) References (once) ----
        ref_user = unique_users[0] if unique_users else str(
            (self.redonline._config.get("defaults") or {}).get("user_id", "584646")
        )
        logger.info("Fetching mapping references using user_id=%s", ref_user)
        try:
            ref_records = [
                coerce_record(i)
                for i in self.redonline.fetch_all(
                    "list_mapping_references",
                    path_vars={"user_id": ref_user},
                )
            ]
        except Exception as exc:  # noqa: BLE001
            logger.warning("References fetch failed: %s", exc)
            ref_records = []
        ref_rows = transform("references", ref_records)
        if want is None or "references" in want:
            result.entities.append(
                self._stage_bundle(
                    name="references",
                    extracted=len(ref_records),
                    table_rows=ref_rows,
                    tables=tables,
                    staging=staging,
                    batch=batch,
                    load_dm=False,
                    loader=None,
                    state=state,
                    watermark_field=None,
                    records=ref_records,
                    details={"user_id": ref_user},
                )
            )

        return result

    def _stage_bundle(
        self,
        *,
        name: str,
        extracted: int,
        table_rows: dict[str, list[dict[str, Any]]],
        tables: dict[str, str],
        staging: RawStaging | None,
        batch: dict[str, Any],
        load_dm: bool,
        loader: DataModelLoader | None,
        state: IngestionState | None,
        watermark_field: str | None,
        records: list[dict[str, Any]],
        details: dict[str, Any],
    ) -> EntityResult:
        er = EntityResult(
            name=name,
            extracted=extracted,
            tables={t: len(rows) for t, rows in table_rows.items()},
            details=details,
        )
        er.staged = sum(er.tables.values())

        if self.dry_run:
            if watermark_field:
                er.watermark = max_watermark(records, watermark_field)
            logger.info(
                "[dry-run] %s extracted=%s would stage %s into RAW %s details=%s",
                name,
                er.extracted,
                er.tables,
                self.settings["raw"]["database"],
                details,
            )
            return er

        assert staging is not None
        written = 0
        for table_key, rows in table_rows.items():
            table_name = tables.get(table_key, table_key)
            written += staging.upsert_rows(
                table_name,
                rows,
                id_field="_raw_key",
                batch_size=int(batch.get("raw_upsert_size", 10000)),
            )
        er.staged = written

        if load_dm and loader is not None and name in {"sites", "users", "tasks"}:
            view_key = {"sites": "site", "users": "user", "tasks": "task"}[name]
            primary = {"sites": "Sites", "users": "Users", "tasks": "Tasks"}[name]
            er.loaded = loader.apply_nodes(
                view_key,
                table_rows.get(primary, []),
                batch_size=int(batch.get("dm_apply_size", 1000)),
            )

        new_wm = (
            max_watermark(records, watermark_field) if watermark_field else None
        )
        if new_wm and state is not None:
            state.set_watermark(
                name,
                new_wm,
                extra={"extracted": er.extracted, "staged": er.staged, "tables": er.tables},
            )
            er.watermark = new_wm

        logger.info("Staged %s -> %s rows across %s", name, er.staged, er.tables)
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
