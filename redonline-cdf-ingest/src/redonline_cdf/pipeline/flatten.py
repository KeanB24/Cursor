"""Flatten ROL API payloads into Cognite RAW table row sets."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_or_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    return value


def flatten_sites(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    pulled = _now()
    for item in records:
        rows.append(
            {
                "_raw_key": str(item.get("id_site")),
                "id_site": item.get("id_site"),
                "id_parent": item.get("id_parent"),
                "name": item.get("name"),
                "id_site_type": item.get("id_site_type"),
                "id_country": item.get("id_country"),
                "id_ref_status": item.get("id_ref_status"),
                "code_iso": item.get("code_iso"),
                "country_name": item.get("country_name"),
                "_source": "ROL",
                "_pulled_at": pulled,
            }
        )
    return {"Sites": rows}


def flatten_users(
    records: list[dict[str, Any]],
    *,
    site_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    site_id = site_id or os.getenv("REDONLINE_SITE_ID") or "112087"
    users: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    pulled = _now()
    for item in records:
        user_id = item.get("id_user")
        users.append(
            {
                "_raw_key": str(user_id),
                "id_user": user_id,
                "firstname": item.get("firstname"),
                "lastname": item.get("lastname"),
                "user_name": item.get("user_name"),
                "email": item.get("email"),
                "id_langue": item.get("id_langue"),
                "language": item.get("language"),
                "locale": item.get("locale"),
                "id_ref_status": item.get("id_ref_status"),
                "id_client": item.get("id_client"),
                "id_site": int(site_id) if str(site_id).isdigit() else site_id,
                "_source": "ROL",
                "_pulled_at": pulled,
            }
        )
        for profile in item.get("profiles") or []:
            if not isinstance(profile, dict):
                continue
            pid = profile.get("id_profile")
            profiles.append(
                {
                    "_raw_key": f"{user_id}_{pid}",
                    "id_user": user_id,
                    "id_profile": pid,
                    "name": profile.get("name"),
                    "_source": "ROL",
                    "_pulled_at": pulled,
                }
            )
    return {"Users": users, "User_profiles": profiles}


def flatten_tasks(
    records: list[dict[str, Any]],
    *,
    user_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    user_id = user_id or os.getenv("REDONLINE_USER_ID") or "584646"
    tasks: list[dict[str, Any]] = []
    instances: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    pulled = _now()

    for task in records:
        task_id = task.get("id")
        tasks.append(
            {
                "_raw_key": str(task_id),
                "id": task_id,
                "title": task.get("title"),
                "description": task.get("description"),
                "type_id": task.get("type_id"),
                "category": task.get("category"),
                "priority": task.get("priority"),
                "recurring_frequency_rule": task.get("recurring_frequency_rule"),
                "recurring_interval_rule": task.get("recurring_interval_rule"),
                "recurring_count_rule": task.get("recurring_count_rule"),
                "recurring_start_date_rule": task.get("recurring_start_date_rule"),
                "recurring_end_date_rule": task.get("recurring_end_date_rule"),
                "due_scheduled_at": task.get("due_scheduled_at"),
                "rescheduled_at": task.get("rescheduled_at"),
                "internal_code": task.get("internal_code"),
                "scope": task.get("scope"),
                "state": task.get("state"),
                "perimeter_state": task.get("perimeter_state"),
                "criticality": task.get("criticality"),
                "temporal_criticality": task.get("temporal_criticality"),
                "created_by": task.get("created_by"),
                "updated_by": task.get("updated_by"),
                "author_name": task.get("author_name"),
                "updater_name": task.get("updater_name"),
                "created_at": task.get("created_at"),
                "updated_at": task.get("updated_at"),
                "created_from": task.get("created_from"),
                "updated_from": task.get("updated_from"),
                "references_nb": task.get("references_nb"),
                "attachments": _json_or_value(task.get("attachments") or []),
                "references": _json_or_value(task.get("references") or []),
                "id_user": int(user_id) if str(user_id).isdigit() else user_id,
                "_source": "ROL",
                "_pulled_at": pulled,
            }
        )

        for inst in task.get("instances") or []:
            if not isinstance(inst, dict):
                continue
            inst_id = inst.get("id")
            site = inst.get("site") or {}
            instances.append(
                {
                    "_raw_key": str(inst_id),
                    "id": inst_id,
                    "task_id": task_id,
                    "state": inst.get("state"),
                    "temporal_criticality": inst.get("temporal_criticality"),
                    "created_by": inst.get("created_by"),
                    "updated_by": inst.get("updated_by"),
                    "id_site": site.get("id_site"),
                    "site_name": site.get("name"),
                    "id_country": site.get("id_country"),
                    "country_name": site.get("country_name"),
                    "site_is_active": site.get("is_active"),
                    "owners": _json_or_value(inst.get("owners") or []),
                    "reviewers": _json_or_value(inst.get("reviewers") or []),
                    "_source": "ROL",
                    "_pulled_at": pulled,
                }
            )
            for occ in inst.get("occurrences") or []:
                if not isinstance(occ, dict):
                    continue
                occ_id = occ.get("id")
                occurrences.append(
                    {
                        "_raw_key": str(occ_id),
                        "id": occ_id,
                        "instance_id": occ.get("instance_id") or inst_id,
                        "task_id": task_id,
                        "due_scheduled_at": occ.get("due_scheduled_at"),
                        "original_due_scheduled_at": occ.get("original_due_scheduled_at"),
                        "completed_at": occ.get("completed_at"),
                        "status_id": occ.get("status_id"),
                        "temporal_criticality": occ.get("temporal_criticality"),
                        "created_by": occ.get("created_by"),
                        "updated_by": occ.get("updated_by"),
                        "attachments": _json_or_value(occ.get("attachments") or []),
                        "feedbacks": _json_or_value(occ.get("feedbacks") or []),
                        "_source": "ROL",
                        "_pulled_at": pulled,
                    }
                )

    return {
        "Tasks": tasks,
        "Task_instances": instances,
        "Task_occurrences": occurrences,
    }


def flatten_references(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Split mapping-references payload into Ref_* lookup tables."""
    pulled = _now()
    payload = records[0] if records else {}
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(data, dict):
        data = {}

    def label_value_rows(items: Any, key_field: str = "value") -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            key = item.get(key_field)
            if key is None:
                continue
            row = {
                "_raw_key": str(key),
                "value": key,
                "label": item.get("label"),
                "_source": "ROL",
                "_pulled_at": pulled,
            }
            for extra in ("reference_type_id", "module_id", "next_status_ids"):
                if extra in item:
                    row[extra] = _json_or_value(item.get(extra))
            rows.append(row)
        return rows

    return {
        "Ref_categories": label_value_rows(data.get("categories")),
        "Ref_priorities": label_value_rows(data.get("priorities")),
        "Ref_states": label_value_rows(data.get("states")),
        "Ref_occurrence_statuses": label_value_rows(data.get("occurrence_statuses")),
    }


def transform(
    name: str,
    records: list[dict[str, Any]],
    *,
    site_id: str | None = None,
    user_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    if name == "sites":
        return flatten_sites(records)
    if name == "users":
        return flatten_users(records, site_id=site_id)
    if name == "tasks":
        return flatten_tasks(records, user_id=user_id)
    if name == "references":
        return flatten_references(records)
    raise KeyError(f"Unknown transform '{name}'")
