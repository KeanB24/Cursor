"""Smoke tests for config loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from redonline_cdf.config import load_endpoints, load_field_maps, load_settings

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _config_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(ROOT / "config"))


def test_load_settings() -> None:
    settings = load_settings()
    assert settings["raw"]["database"] == "ROL-COR"
    assert settings["raw"]["tables"]["Sites"] == "Sites"
    assert settings["raw"]["tables"]["Tasks"] == "Tasks"
    assert settings["load_to_data_model"] is False
    assert settings["ingest_mode"] == "cascaded"


def test_load_endpoints() -> None:
    endpoints = load_endpoints()
    assert endpoints["base_url"] == "https://apigw.ct-test.hse-compliance.net"
    assert endpoints["endpoints"]["list_sites"]["items_path"] == "sites"
    assert endpoints["endpoints"]["list_tasks_by_user"]["items_path"] == "data"


def test_load_field_maps() -> None:
    maps = load_field_maps()
    assert "task" in maps
    assert maps["constants"]["_source_system"] == "ROL"
