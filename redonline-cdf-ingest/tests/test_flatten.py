"""Unit tests for ROL → RAW flatten transformers."""

from __future__ import annotations

from redonline_cdf.pipeline.flatten import (
    flatten_references,
    flatten_sites,
    flatten_tasks,
    flatten_users,
)


def test_flatten_sites() -> None:
    out = flatten_sites(
        [{"id_site": 112087, "name": "GEL", "id_parent": 1, "code_iso": "NL"}]
    )
    assert "Sites" in out
    assert out["Sites"][0]["_raw_key"] == "112087"
    assert out["Sites"][0]["name"] == "GEL"


def test_flatten_users_and_profiles() -> None:
    out = flatten_users(
        [
            {
                "id_user": 1,
                "email": "a@b.com",
                "profiles": [{"id_profile": 5, "name": "P5"}],
            }
        ],
        site_id="112087",
    )
    assert out["Users"][0]["id_site"] == 112087
    assert out["User_profiles"][0]["_raw_key"] == "1_5"


def test_flatten_tasks_nested() -> None:
    out = flatten_tasks(
        [
            {
                "id": 10,
                "title": "T",
                "updated_at": "2026-01-01T00:00:00Z",
                "instances": [
                    {
                        "id": 20,
                        "state": 2,
                        "site": {"id_site": 99, "name": "S"},
                        "occurrences": [{"id": 30, "instance_id": 20, "status_id": 1}],
                    }
                ],
            }
        ],
        user_id="584646",
    )
    assert out["Tasks"][0]["_raw_key"] == "10"
    assert out["Task_instances"][0]["id_site"] == 99
    assert out["Task_occurrences"][0]["_raw_key"] == "30"


def test_flatten_references_lookups() -> None:
    out = flatten_references(
        [
            {
                "success": True,
                "data": {
                    "categories": [{"label": "c", "value": 2}],
                    "priorities": [{"label": "p", "value": 1}],
                    "states": [{"label": "s", "value": 2}],
                    "occurrence_statuses": [
                        {"label": "n", "value": 1, "next_status_ids": [2]}
                    ],
                },
            }
        ]
    )
    assert out["Ref_categories"][0]["_raw_key"] == "2"
    assert out["Ref_priorities"][0]["value"] == 1
    assert out["Ref_states"][0]["label"] == "s"
    assert out["Ref_occurrence_statuses"][0]["next_status_ids"] == [2]
