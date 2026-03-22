# Docker Compose Manager

A FastAPI web app for registering folders that contain Docker Compose files and controlling them from a clean dashboard.

## Features

- iPhone-style app grid on the front page
- Auto-discover mounted app folders inside `/apps`
- Per-app settings for icon, color, notes, and unlimited service links
- Docker actions: up, down, pull, restart, and pull + recreate
- Status overview with service state and health when Docker exposes it

## Run locally

The project supports `.env`-based dev mode. With `DEV_MODE=true`, the app scans [`/Users/oliver/Documents/Dev/DockerManager/.apps`](/Users/oliver/Documents/Dev/DockerManager/.apps) instead of `/apps`.

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start the app:

```bash
uvicorn app.main:app --reload
```

3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

4. Put local test stacks inside:

```text
.apps/
  jellyfin/
  radarr/
  nextcloud/
```

## Build and upload the Docker image

1. Build the image and upload to docker hub:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t drevoliv/compose-manager:latest --push .
```

2. Pull it anywhere:

```bash
docker pull your-dockerhub-username/compose-manager:latest
```

## Run the image

Recommended host-control run:

```bash
docker run -p 8000:8000 \
  -e APPS_ROOT=/apps \
  -v "$(pwd)/data:/app/data" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /srv/apps:/apps \
  your-dockerhub-username/compose-manager:latest
```

The app scans subfolders inside `/apps` and auto-adds them to the dashboard.

Example:

```text
/srv/apps/jellyfin
/srv/apps/nextcloud
/srv/apps/radarr
```

Each of those folders should contain a compose file with a common name like `compose.yaml` or `docker-compose.yml`. If a folder uses a custom compose filename, the app still gets discovered and you can set the filename later in that app's settings.

You cannot mount two different host folders to the exact same container path like this:

```bash
-v ./service1:/apps
-v ./service2:/apps
```

The second mount hides the first one.

Use one parent folder:

```bash
-v /srv/apps:/apps
```

Or mount each service to its own subfolder:

```bash
-v ./service1:/apps/service1
-v ./service2:/apps/service2
```

## Notes

- The app stores registered compose folders in [`data/apps.json`](/Users/oliver/Documents/Dev/DockerManager/data/apps.json).
- Compose commands run through `docker compose` or `docker-compose`, depending on what is available in the container.
- Health badges depend on what `docker compose ps --format json` reports for each service.
