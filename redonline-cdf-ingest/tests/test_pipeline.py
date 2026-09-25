"""Pipeline dry-run tests with mocked Red Online fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from redonline_cdf.cognite.dm_loader import DataModelLoader
from redonline_cdf.config import load_field_maps, load_settings
from redonline_cdf.pipeline.ingest import IngestPipeline
from redonline_cdf.pipeline.state import max_watermark
from redonline_cdf.redonline.client import RedOnlineClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _config_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(ROOT / "config"))


def test_max_watermark() -> None:
    rows = [
        {"updatedAt": "2026-03-10T00:00:00Z"},
        {"updatedAt": "2026-03-18T14:30:00Z"},
        {"updatedAt": "2026-03-15T10:00:00Z"},
    ]
    assert max_watermark(rows, "updatedAt") == "2026-03-18T14:30:00Z"


def test_pipeline_dry_run_with_fixtures() -> None:
    red = RedOnlineClient(mock=True, fixtures_dir=ROOT / "fixtures")
    pipeline = IngestPipeline(cognite=None, redonline=red, dry_run=True)
    result = pipeline.run()
    red.close()

    assert result.dry_run is True
    by_name = {e.name: e for e in result.entities}
    assert by_name["actions"].extracted == 2
    assert by_name["tasks"].extracted == 2
    assert by_name["categories"].extracted == 2
    assert by_name["actions"].watermark == "2026-03-18T14:30:00Z"


def test_dm_loader_build_nodes() -> None:
    settings = load_settings()
    field_maps = load_field_maps()
    client = MagicMock()
    loader = DataModelLoader(
        client,
        instance_space=settings["data_model"]["instance_space"],
        views=settings["data_model"]["views"],
        field_maps=field_maps,
    )
    rows = [
        {
            "id": "ACT-1001",
            "title": "Investigate",
            "status": "Open",
            "_source_system": "RedOnline",
        }
    ]
    nodes = loader.build_nodes("action", rows)
    assert len(nodes) == 1
    assert nodes[0].external_id == "ACT-1001"
    assert nodes[0].space == "ac_action_item_management"
    assert nodes[0].sources[0].properties["title"] == "Investigate"


def test_field_maps_align_with_settings() -> None:
    settings = load_settings()
    field_maps = load_field_maps()
    for entity in settings["entities"]:
        assert entity["view_key"] in field_maps
