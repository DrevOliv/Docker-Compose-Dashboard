# Compose Manager

Compose Manager is a FastAPI web application for discovering, monitoring, and controlling Docker Compose stacks from a single interface.

It is designed for self-hosted environments where multiple services live in mounted folders on the host. The application scans those folders for Compose files, adds each stack to a dashboard automatically, and lets you manage each app from a clean web UI.

## What it does

- Discovers Docker Compose apps automatically from a mounted apps directory
- Shows stacks in a visual app-style dashboard
- Displays runtime state and service health when Docker reports it
- Supports common stack actions from the UI:
  - Start
  - Stop
  - Restart
  - Update
- Lets you customize each app with:
  - Name
  - Icon
  - Accent color
  - Notes
  - Service links
- Handles missing folders gracefully by marking apps as unavailable instead of failing silently

## How discovery works

Compose Manager scans the configured apps root and searches recursively for folders that contain a standard Docker Compose filename:

- `compose.yaml`
- `compose.yml`
- `docker-compose.yaml`
- `docker-compose.yml`

If a Compose file is found in:

```text
/apps/media/jellyfin/docker-compose.yml
/apps/media/radarr/compose.yaml
```

the dashboard will show:

- `jellyfin`
- `radarr`

The app name is based on the folder that contains the Compose file.

If a stack uses a non-standard Compose filename, it can still be added and configured later through the app settings.

## Requirements

- Python 3.12+ for local development
- Docker and Docker Compose access on the target host
- A mounted apps directory that the container can read
- Access to `/var/run/docker.sock` if you want the UI to control the host Docker engine

## Run locally

Local development uses `.env` and supports a development apps root.

With `DEV_MODE=true`, the app scans the local [`/Users/oliver/Documents/Dev/DockerManager/.apps`](/Users/oliver/Documents/Dev/DockerManager/.apps) directory instead of `/apps`.

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
uvicorn app.main:app --reload
```

### 4. Open the UI

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 5. Add local test stacks

Example:

```text
.apps/
  media/
    jellyfin/
      docker-compose.yml
    radarr/
      compose.yaml
  cloud/
    nextcloud/
      docker-compose.yml
```

## Run with Docker

This is the recommended deployment model.

The container:

- serves the web UI
- scans a mounted apps directory
- talks to the host Docker engine through the Docker socket

### Recommended run command

```bash
docker run -d \
  --name compose-manager \
  -p 8000:8000 \
  -e APPS_ROOT=/apps \
  -v "$(pwd)/data:/app/data" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /srv/apps:/apps \
  your-dockerhub-username/compose-manager:latest
```

Or using the docker compose example

Then open:

[http://localhost:8000](http://localhost:8000)

### Example host folder layout

```text
/srv/apps/
  media/
    jellyfin/
      docker-compose.yml
    radarr/
      compose.yaml
  cloud/
    nextcloud/
      docker-compose.yml
```

## Important volume note

Do not mount multiple host folders to the same container path:

```bash
-v ./service1:/apps
-v ./service2:/apps
```

The second mount hides the first one.

Use either:

```bash
-v /srv/apps:/apps
```

or distinct subpaths:

```bash
-v ./service1:/apps/service1
-v ./service2:/apps/service2
```

# Dev tips

## Build the Docker image

Build locally:

```bash
docker build -t your-dockerhub-username/compose-manager:latest .
```

Build and push multi-arch with Buildx:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t your-dockerhub-username/compose-manager:latest \
  --push .
```

Pull later with:

```bash
docker pull your-dockerhub-username/compose-manager:latest
```

## Data storage

Application metadata is stored in:

[`/Users/oliver/Documents/Dev/DockerManager/data/apps.json`](/Users/oliver/Documents/Dev/DockerManager/data/apps.json)

This file contains app configuration such as:

- display name
- selected icon
- accent color
- notes
- service links

## Notes

- Compose Manager uses `docker compose` when available and falls back to `docker-compose` if needed.
- Service health depends on what Docker reports through `docker compose ps --format json`.
- If an app folder disappears, the dashboard keeps the app visible and marks it as missing.
