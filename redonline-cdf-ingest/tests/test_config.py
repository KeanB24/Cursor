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
    assert settings["raw"]["database"] == "redonline_staging"
    assert len(settings["entities"]) == 4


def test_load_endpoints() -> None:
    endpoints = load_endpoints()
    assert endpoints["auth"]["header_name"] == "X-ROL-API-KEY"
    assert endpoints["auth"]["style"] == "header"
    names = set(endpoints["endpoints"])
    assert names == {
        "list_sites",
        "list_users_by_site",
        "list_mapping_references",
        "list_tasks_by_user",
    }


def test_load_field_maps() -> None:
    maps = load_field_maps()
    assert "task" in maps
    assert "site" in maps
    assert maps["constants"]["_source_system"] == "RedOnline"
