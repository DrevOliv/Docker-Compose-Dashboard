from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import AppCreate, AppEntry, AppUpdate, DashboardData


class AppStore:
    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file.exists():
            self.save(DashboardData())

    def load(self) -> DashboardData:
        raw = json.loads(self.data_file.read_text(encoding="utf-8"))
        return DashboardData.model_validate(raw)

    def save(self, data: DashboardData) -> None:
        self.data_file.write_text(
            json.dumps(data.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

    def list_apps(self) -> list[AppEntry]:
        return self.load().apps

    def get_app(self, app_id: str) -> AppEntry | None:
        return next((app for app in self.load().apps if app.id == app_id), None)

    def create_app(self, payload: AppCreate) -> AppEntry:
        data = self.load()
        now = datetime.now(timezone.utc)
        app = AppEntry(
            id=uuid4().hex[:12],
            name=payload.name.strip(),
            folder_path=payload.folder_path.strip(),
            compose_file=payload.compose_file.strip() if payload.compose_file else None,
            icon=payload.icon,
            color=payload.color,
            links=payload.links,
            notes=payload.notes.strip(),
            created_at=now,
            updated_at=now,
        )
        data.apps.append(app)
        self.save(data)
        return app

    def update_app(self, app_id: str, payload: AppUpdate) -> AppEntry | None:
        data = self.load()
        now = datetime.now(timezone.utc)
        for idx, app in enumerate(data.apps):
            if app.id != app_id:
                continue
            updated = app.model_copy(
                update={
                    "name": payload.name.strip(),
                    "folder_path": payload.folder_path.strip(),
                    "compose_file": payload.compose_file.strip() if payload.compose_file else None,
                    "icon": payload.icon,
                    "color": payload.color,
                    "links": payload.links,
                    "notes": payload.notes.strip(),
                    "updated_at": now,
                }
            )
            data.apps[idx] = updated
            self.save(data)
            return updated
        return None

    def delete_app(self, app_id: str) -> bool:
        data = self.load()
        original_len = len(data.apps)
        data.apps = [app for app in data.apps if app.id != app_id]
        if len(data.apps) == original_len:
            return False
        self.save(data)
        return True
