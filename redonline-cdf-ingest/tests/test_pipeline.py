"""Pipeline dry-run tests with mocked Red Online fixtures (cascaded)."""

from __future__ import annotations

from pathlib import Path

import pytest

from redonline_cdf.pipeline.ingest import IngestPipeline
from redonline_cdf.redonline.client import RedOnlineClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _config_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(ROOT / "config"))


def test_pipeline_cascaded_dry_run_with_fixtures() -> None:
    settings = {
        "raw": {
            "database": "ROL-COR",
            "tables": {
                "Sites": "Sites",
                "Users": "Users",
                "User_profiles": "User_profiles",
                "Tasks": "Tasks",
                "Task_instances": "Task_instances",
                "Task_occurrences": "Task_occurrences",
                "Ref_categories": "Ref_categories",
                "Ref_priorities": "Ref_priorities",
                "Ref_states": "Ref_states",
                "Ref_occurrence_statuses": "Ref_occurrence_statuses",
                "Ingestion_state": "Ingestion_state",
            },
        },
        "load_to_data_model": False,
        "ingest_mode": "cascaded",
        "cascaded": {
            "max_sites": 2,
            "max_users_per_site": 2,
            "max_users_for_tasks": 2,
        },
        "batch": {"raw_upsert_size": 10000, "dm_apply_size": 1000},
        "data_model": {"instance_space": "x", "views": {}},
    }
    red = RedOnlineClient(mock=True, fixtures_dir=ROOT / "fixtures")
    pipeline = IngestPipeline(
        cognite=None,
        redonline=red,
        settings=settings,
        dry_run=True,
    )
    result = pipeline.run()
    red.close()

    assert result.mode == "cascaded"
    assert result.database == "ROL-COR"
    by_name = {e.name: e for e in result.entities}
    assert by_name["sites"].tables["Sites"] == 2
    assert by_name["users"].tables["Users"] >= 1
    assert by_name["users"].details["sites_queried"] == 2
    assert by_name["tasks"].tables["Tasks"] >= 1
    assert by_name["tasks"].details["users_queried"] >= 1
    assert by_name["references"].tables["Ref_categories"] >= 1
