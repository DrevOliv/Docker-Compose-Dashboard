from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from .docker_ops import ComposeError, detect_default_compose_file, get_runtime_status, run_action
from .models import AppCreate, AppUpdate, ComposeActionRequest
from .store import AppStore

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
STORE = AppStore(DATA_DIR / "apps.json")
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in {"1", "true", "yes", "on"}
DEFAULT_APPS_ROOT = BASE_DIR / "apps" if DEV_MODE else Path("/apps")
APPS_ROOT = Path(os.getenv("APPS_ROOT", str(DEFAULT_APPS_ROOT))).expanduser()

app = FastAPI(title="Docker Compose Manager")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def serialize_dashboard_apps() -> list[dict]:
    apps = []
    for item in STORE.list_apps():
        runtime = get_runtime_status(item)
        app_payload = item.model_dump(mode="json")
        app_payload["runtime"] = runtime.model_dump(mode="json")
        apps.append(app_payload)
    return apps


def discover_mounted_apps() -> list[dict[str, str | None]]:
    if not APPS_ROOT.exists() or not APPS_ROOT.is_dir():
        return []

    discovered: list[dict[str, str | None]] = []
    seen_paths: set[str] = set()
    for entry in sorted(APPS_ROOT.rglob("*"), key=lambda item: str(item).lower()):
        if not entry.is_dir():
            continue
        compose_file = detect_default_compose_file(entry)
        if compose_file is None:
            continue
        folder_path = str(entry)
        if folder_path in seen_paths:
            continue
        seen_paths.add(folder_path)
        discovered.append(
            {
                "folder_path": folder_path,
                "compose_file": compose_file.name,
            }
        )
    return discovered


def sync_mounted_apps() -> None:
    STORE.sync_discovered_apps(discover_mounted_apps())


def validate_compose_payload(folder_path: str, compose_file: str | None) -> None:
    folder = Path(folder_path).expanduser()
    if not folder.exists() or not folder.is_dir():
        raise HTTPException(status_code=400, detail="Folder path was not found.")

    if compose_file:
        candidate = folder / compose_file
        if not candidate.exists():
            raise HTTPException(status_code=400, detail="That compose filename was not found in the folder.")
        return

    if detect_default_compose_file(folder) is None:
        raise HTTPException(
            status_code=400,
            detail="No common compose filename was found. Enter the compose filename manually.",
        )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    sync_mounted_apps()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "apps": serialize_dashboard_apps(),
            "apps_root": str(APPS_ROOT),
        },
    )


@app.get("/apps/{app_id}", response_class=HTMLResponse)
async def app_detail(request: Request, app_id: str) -> HTMLResponse:
    sync_mounted_apps()
    app_entry = STORE.get_app(app_id)
    if app_entry is None:
        raise HTTPException(status_code=404, detail="App not found.")
    runtime = get_runtime_status(app_entry)
    return templates.TemplateResponse(
        "app_detail.html",
        {
            "request": request,
            "app_item": app_entry.model_dump(mode="json"),
            "runtime": runtime.model_dump(mode="json"),
        },
    )


@app.get("/api/apps")
async def list_apps() -> dict:
    sync_mounted_apps()
    return {"apps": serialize_dashboard_apps()}


@app.post("/api/discovery/sync")
async def sync_apps() -> dict:
    sync_mounted_apps()
    return {"ok": True, "apps": serialize_dashboard_apps()}


@app.post("/api/apps", status_code=201)
async def create_app(payload: AppCreate) -> dict:
    validate_compose_payload(payload.folder_path, payload.compose_file)
    entry = STORE.create_app(payload)
    runtime = get_runtime_status(entry)
    return {"app": entry.model_dump(mode="json"), "runtime": runtime.model_dump(mode="json")}


@app.put("/api/apps/{app_id}")
async def update_app(app_id: str, payload: AppUpdate) -> dict:
    validate_compose_payload(payload.folder_path, payload.compose_file)
    entry = STORE.update_app(app_id, payload)
    if entry is None:
        raise HTTPException(status_code=404, detail="App not found.")
    runtime = get_runtime_status(entry)
    return {"app": entry.model_dump(mode="json"), "runtime": runtime.model_dump(mode="json")}


@app.delete("/api/apps/{app_id}", status_code=204)
async def delete_app(app_id: str) -> JSONResponse:
    deleted = STORE.delete_app(app_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="App not found.")
    return JSONResponse(status_code=204, content=None)


@app.post("/api/apps/{app_id}/actions")
async def app_action(app_id: str, payload: ComposeActionRequest) -> dict:
    app_entry = STORE.get_app(app_id)
    if app_entry is None:
        raise HTTPException(status_code=404, detail="App not found.")
    try:
        output = run_action(app_entry, payload.action)
        runtime = get_runtime_status(app_entry)
        return {
            "ok": True,
            "message": output or f"Action '{payload.action}' completed.",
            "runtime": runtime.model_dump(mode="json"),
        }
    except ComposeError as exc:
        runtime = get_runtime_status(app_entry)
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "runtime": runtime.model_dump(mode="json"),
            },
        ) from exc


@app.get("/api/apps/{app_id}/status")
async def app_status(app_id: str) -> dict:
    app_entry = STORE.get_app(app_id)
    if app_entry is None:
        raise HTTPException(status_code=404, detail="App not found.")
    runtime = get_runtime_status(app_entry)
    return {"runtime": runtime.model_dump(mode="json")}
