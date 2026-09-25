"""Load YAML configuration for the ingest pipeline."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def project_root() -> Path:
    """Return the repository root (parent of config/)."""
    # Prefer CONFIG_DIR parent when set; otherwise walk up from this file.
    env_dir = os.getenv("CONFIG_DIR")
    if env_dir:
        return Path(env_dir).resolve().parent
    return Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    env_dir = os.getenv("CONFIG_DIR")
    if env_dir:
        return Path(env_dir).resolve()
    return project_root() / "config"


def load_yaml(name: str) -> dict[str, Any]:
    path = config_dir() / name
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}, got {type(data)}")
    return data


def load_settings() -> dict[str, Any]:
    return load_yaml("settings.yaml")


def load_endpoints() -> dict[str, Any]:
    return load_yaml("endpoints.yaml")


def load_field_maps() -> dict[str, Any]:
    return load_yaml("field_maps.yaml")
