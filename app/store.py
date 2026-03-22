from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .models import AppCreate, AppEntry, AppUpdate, DashboardData

DEFAULT_DISCOVERY_ICONS = (
    "cube",
    "server",
    "database",
    "cloud",
    "shield",
    "world",
    "home",
    "settings",
    "tool",
    "tools",
    "wrench",
    "terminal-2",
    "command",
    "brand-docker",
    "brand-youtube",
    "device-tv",
    "device-desktop",
    "device-laptop",
    "router",
    "wifi",
    "player-play",
    "movie",
    "photo",
    "camera",
    "music",
    "disc",
    "cast",
    "apps",
    "layout-dashboard",
    "layout-grid",
    "stack-2",
    "package",
    "archive",
    "folder",
    "folders",
    "file-text",
    "download",
    "upload",
    "refresh",
    "activity",
    "bolt",
    "flame",
    "rocket",
    "star",
    "heart",
    "lock",
    "key",
    "search",
    "chart-bar",
    "chart-pie",
    "cpu",
)


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

    def random_color(self) -> str:
        hue = random.randint(0, 359)
        saturation = random.randint(65, 84)
        lightness = random.randint(45, 54)
        return self.hsl_to_hex(hue, saturation, lightness)

    @staticmethod
    def hsl_to_hex(h: int, s: int, l: int) -> str:
        s = s / 100
        l = l / 100

        def k(n: int) -> float:
            return (n + h / 30) % 12

        a = s * min(l, 1 - l)

        def f(n: int) -> str:
            channel = round(255 * (l - a * max(-1, min(k(n) - 3, min(9 - k(n), 1)))))
            return f"{channel:02x}"

        return f"#{f(0)}{f(8)}{f(4)}"

    def random_icon(self) -> str:
        return random.choice(DEFAULT_DISCOVERY_ICONS)

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
            source="manual",
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

    def sync_discovered_apps(self, discovered_apps: list[dict[str, str | None]]) -> bool:
        data = self.load()
        known_by_path = {app.folder_path: app for app in data.apps}
        discovered_paths = {str(item["folder_path"]) for item in discovered_apps}
        changed = False
        now = datetime.now(timezone.utc)

        for discovered in discovered_apps:
            folder_path = str(discovered["folder_path"])
            compose_file = discovered.get("compose_file")
            existing = known_by_path.get(folder_path)
            if existing is None:
                data.apps.append(
                    AppEntry(
                        id=uuid4().hex[:12],
                        name=Path(folder_path).name,
                        folder_path=folder_path,
                        compose_file=str(compose_file) if compose_file else None,
                        source="mounted",
                        icon=self.random_icon(),
                        color=self.random_color(),
                        created_at=now,
                        updated_at=now,
                    )
                )
                changed = True
                continue

            if existing.compose_file is None and compose_file:
                updated = existing.model_copy(
                    update={
                        "compose_file": str(compose_file),
                        "updated_at": now,
                    }
                )
                index = data.apps.index(existing)
                data.apps[index] = updated
                changed = True

        filtered_apps = []
        for app in data.apps:
            if app.source == "mounted" and app.folder_path not in discovered_paths:
                changed = True
                continue
            filtered_apps.append(app)
        data.apps = filtered_apps

        if changed:
            self.save(data)
        return changed

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
