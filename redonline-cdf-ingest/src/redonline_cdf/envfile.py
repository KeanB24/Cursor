"""Load project `.env` (and parent workspace `.env`) as the credential source of truth."""

from __future__ import annotations

import os
from pathlib import Path


def candidate_env_paths(project_root: Path) -> list[Path]:
    """Return `.env` paths in priority order (first wins for each key)."""
    root = project_root.resolve()
    return [
        root / ".env",
        root.parent / ".env",  # workspace / office Cursor folder
    ]


def load_env_files(project_root: Path) -> list[Path]:
    """
    Load `.env` from the project folder, then the parent workspace folder.

    Existing process env vars are not overwritten. Project `.env` takes
    precedence over the parent file for keys present in both.
    """
    loaded: list[Path] = []
    for path in candidate_env_paths(project_root):
        if not path.is_file():
            continue
        _load_one(path)
        loaded.append(path)
    return loaded


def _load_one(env_path: Path) -> None:
    try:
        from dotenv import load_dotenv

        try:
            load_dotenv(env_path, encoding="utf-8-sig", override=False)
            return
        except TypeError:
            load_dotenv(env_path, override=False)
            return
    except ImportError:
        pass

    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
