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
    assert len(settings["entities"]) == 3


def test_load_endpoints() -> None:
    endpoints = load_endpoints()
    assert "list_actions" in endpoints["endpoints"]


def test_load_field_maps() -> None:
    maps = load_field_maps()
    assert "action" in maps
    assert maps["constants"]["_source_system"] == "RedOnline"
