from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .models import AppEntry, AppRuntimeStatus, ComposeServiceStatus

DEFAULT_COMPOSE_FILES = (
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
)


class ComposeError(RuntimeError):
    pass


def resolve_compose_binary() -> list[str]:
    docker_bin = shutil.which("docker")
    if docker_bin:
        return [docker_bin, "compose"]
    docker_compose_bin = shutil.which("docker-compose")
    if docker_compose_bin:
        return [docker_compose_bin]
    raise ComposeError("Docker Compose is not installed in the container.")


def detect_default_compose_file(folder_path: str | Path) -> Path | None:
    folder = Path(folder_path).expanduser()
    for name in DEFAULT_COMPOSE_FILES:
        candidate = folder / name
        if candidate.exists():
            return candidate
    return None


def resolve_compose_file(app: AppEntry) -> Path | None:
    folder = Path(app.folder_path).expanduser()
    if app.compose_file:
        candidate = folder / app.compose_file
        return candidate if candidate.exists() else None
    return detect_default_compose_file(folder)


def build_compose_command(app: AppEntry, *args: str) -> tuple[list[str], Path]:
    folder = Path(app.folder_path).expanduser()
    compose_file = resolve_compose_file(app)
    if not folder.exists():
        raise ComposeError(f"Folder does not exist: {folder}")
    if compose_file is None:
        raise ComposeError("No docker compose file was found in this folder.")

    cmd = [*resolve_compose_binary(), "-f", str(compose_file), *args]
    return cmd, folder


def run_compose(app: AppEntry, *args: str) -> str:
    cmd, cwd = build_compose_command(app, *args)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip() or "Unknown compose error."
        raise ComposeError(error)
    return result.stdout.strip()


def run_action(app: AppEntry, action: str) -> str:
    if action == "up":
        return run_compose(app, "up", "-d")
    if action == "down":
        return run_compose(app, "down")
    if action == "pull":
        return run_compose(app, "pull")
    if action == "restart":
        return run_compose(app, "restart")
    if action == "refresh":
        output = run_compose(app, "pull")
        clear_output = run_compose(app, "down", "--rmi", "all")
        up_output = run_compose(app, "up", "-d")
        return "\n".join(part for part in (output, up_output, clear_output) if part)
    raise ComposeError(f"Unsupported action: {action}")


def get_runtime_status(app: AppEntry) -> AppRuntimeStatus:
    checked_at = datetime.now(timezone.utc)
    folder = Path(app.folder_path).expanduser()
    if not folder.exists():
        return AppRuntimeStatus(
            folder_exists=False,
            overall_state="missing",
            health="missing",
            compose_detected=False,
            compose_file=None,
            error="Folder not found.",
            last_checked=checked_at,
        )

    compose_file = resolve_compose_file(app)
    if compose_file is None:
        return AppRuntimeStatus(
            folder_exists=True,
            compose_detected=False,
            compose_file=None,
            error="Compose file not found.",
            last_checked=checked_at,
        )

    try:
        output = run_compose(app, "ps", "--format", "json")
    except ComposeError as exc:
        return AppRuntimeStatus(
            folder_exists=True,
            compose_detected=True,
            compose_file=str(compose_file),
            error=str(exc),
            last_checked=checked_at,
        )

    services: list[ComposeServiceStatus] = []
    if output:
        try:
            decoded = json.loads(output)
            if isinstance(decoded, dict):
                decoded = [decoded]
        except json.JSONDecodeError:
            decoded = []
    else:
        decoded = []

    for item in decoded:
        health = item.get("Health") or item.get("health") or "unknown"
        state = item.get("State") or item.get("state") or "unknown"
        publishers = item.get("Publishers") or item.get("publishers") or []
        ports: list[str] = []
        for publisher in publishers:
            published = publisher.get("PublishedPort")
            target = publisher.get("TargetPort")
            protocol = publisher.get("Protocol", "tcp")
            if published and target:
                ports.append(f"{published}->{target}/{protocol}")
        services.append(
            ComposeServiceStatus(
                name=item.get("Service") or item.get("Name") or "unknown",
                state=state.lower(),
                health=str(health).lower(),
                published_ports=ports,
            )
        )

    overall_state = derive_overall_state(services)
    health = derive_health(services)
    return AppRuntimeStatus(
        folder_exists=True,
        overall_state=overall_state,
        health=health,
        compose_detected=True,
        compose_file=str(compose_file),
        services=services,
        last_checked=checked_at,
    )


def derive_overall_state(services: list[ComposeServiceStatus]) -> str:
    if not services:
        return "stopped"
    states = {service.state for service in services}
    if all(state == "running" for state in states):
        return "running"
    if "running" in states:
        return "partial"
    return next(iter(states), "unknown")


def derive_health(services: list[ComposeServiceStatus]) -> str:
    if not services:
        return "unknown"
    healths = {service.health for service in services}
    if "unhealthy" in healths:
        return "unhealthy"
    if "starting" in healths:
        return "starting"
    if healths == {"healthy"}:
        return "healthy"
    if "healthy" in healths and len(healths) > 1:
        return "degraded"
    if healths == {"unknown"}:
        running_states = {service.state for service in services}
        if running_states == {"running"}:
            return "running"
    return next(iter(healths), "unknown")
