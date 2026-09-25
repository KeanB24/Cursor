"""Unit tests for field mapping and dig helper."""

from __future__ import annotations

from redonline_cdf.cognite.dm_loader import map_row_to_properties
from redonline_cdf.redonline.client import dig


def test_dig_nested_path() -> None:
    payload = {"data": {"items": [{"id": "1"}], "nextPageToken": "abc"}}
    assert dig(payload, "data.items") == [{"id": "1"}]
    assert dig(payload, "data.nextPageToken") == "abc"
    assert dig(payload, "missing.path") is None


def test_map_row_to_properties() -> None:
    field_map = {
        "externalId": "id",
        "properties": {
            "title": "title",
            "status": "status",
            "sourceSystem": "_source_system",
        },
    }
    row = {"id": "ACT-1", "title": "Test", "status": "Open"}
    external_id, props = map_row_to_properties(
        row, field_map, constants={"_source_system": "RedOnline"}
    )
    assert external_id == "ACT-1"
    assert props == {
        "title": "Test",
        "status": "Open",
        "sourceSystem": "RedOnline",
    }


def test_map_row_skips_missing_values() -> None:
    field_map = {
        "externalId": "id",
        "properties": {"title": "title", "assignee": "assignee"},
    }
    row = {"id": "ACT-2", "title": "Only title"}
    _, props = map_row_to_properties(row, field_map)
    assert props == {"title": "Only title"}
    assert "assignee" not in props
