"""Pydantic DTOs for Red Online EHS entities (placeholder fields)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Action(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    title: str | None = None
    description: str | None = None
    status: str | None = None
    category_id: str | None = Field(default=None, alias="categoryId")
    due_date: str | None = Field(default=None, alias="dueDate")
    priority: str | None = None
    assignee: str | None = None
    updated_at: str | None = Field(default=None, alias="updatedAt")
    created_at: str | None = Field(default=None, alias="createdAt")


class Task(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    title: str | None = None
    description: str | None = None
    status: str | None = None
    action_id: str | None = Field(default=None, alias="actionId")
    due_date: str | None = Field(default=None, alias="dueDate")
    assignee: str | None = None
    updated_at: str | None = Field(default=None, alias="updatedAt")
    created_at: str | None = Field(default=None, alias="createdAt")


class Category(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    name: str | None = None
    code: str | None = None
    description: str | None = None
    updated_at: str | None = Field(default=None, alias="updatedAt")


def coerce_record(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a Red Online item to a flat string-keyed dict for RAW staging."""
    out: dict[str, Any] = {}
    for key, value in data.items():
        if value is None:
            out[key] = None
        elif isinstance(value, (dict, list)):
            out[key] = value
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out
