from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class ServiceLink(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    url: str = Field(min_length=1, max_length=500)


class AppEntry(BaseModel):
    id: str
    name: str = Field(min_length=1, max_length=120)
    folder_path: str = Field(min_length=1)
    compose_file: str | None = None
    icon: str = Field(default="cube")
    color: str = Field(default="#2563eb")
    links: list[ServiceLink] = Field(default_factory=list)
    notes: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AppCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    folder_path: str = Field(min_length=1)
    compose_file: str | None = None
    icon: str = Field(default="cube")
    color: str = Field(default="#2563eb")
    links: list[ServiceLink] = Field(default_factory=list)
    notes: str = Field(default="")


class AppUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    folder_path: str = Field(min_length=1)
    compose_file: str | None = None
    icon: str = Field(default="cube")
    color: str = Field(default="#2563eb")
    links: list[ServiceLink] = Field(default_factory=list)
    notes: str = Field(default="")


class ComposeActionRequest(BaseModel):
    action: Literal["up", "down", "pull", "restart", "refresh"]


class ComposeServiceStatus(BaseModel):
    name: str
    state: str
    health: str = "unknown"
    published_ports: list[str] = Field(default_factory=list)


class AppRuntimeStatus(BaseModel):
    overall_state: str = "unknown"
    health: str = "unknown"
    compose_detected: bool = False
    compose_file: str | None = None
    services: list[ComposeServiceStatus] = Field(default_factory=list)
    last_checked: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error: str | None = None


class DashboardData(BaseModel):
    apps: list[AppEntry] = Field(default_factory=list)
