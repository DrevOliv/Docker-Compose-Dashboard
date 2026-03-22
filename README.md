# Docker Compose Manager

A FastAPI web app for registering folders that contain Docker Compose files and controlling them from a clean dashboard.

## Features

- iPhone-style app grid on the front page
- Add folders with `compose.yaml` or `docker-compose.yml`
- Per-app settings for icon, color, notes, and unlimited service links
- Docker actions: up, down, pull, restart, and pull + recreate
- Status overview with service state and health when Docker exposes it

## Run locally

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

## Build and upload the Docker image

1. Build the image:

```bash
docker build -t docker-compose-manager:latest .
```

2. Tag it for Docker Hub:

```bash
docker tag docker-compose-manager:latest your-dockerhub-username/docker-compose-manager:latest
```

3. Log in to Docker Hub:

```bash
docker login
```

4. Push the image:

```bash
docker push your-dockerhub-username/docker-compose-manager:latest
```

5. Pull it anywhere:

```bash
docker pull your-dockerhub-username/docker-compose-manager:latest
```

## Run the image

Basic run:

```bash
docker run -p 8000:8000 -v "$(pwd)/data:/app/data" your-dockerhub-username/docker-compose-manager:latest
```

If you want the app to manage Docker on the same host, mount the Docker socket too:

```bash
docker run -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  your-dockerhub-username/docker-compose-manager:latest
```

## Notes

- The app stores registered compose folders in [`data/apps.json`](/Users/oliver/Documents/Dev/DockerManager/data/apps.json).
- Compose commands run through `docker compose`.
- Health badges depend on what `docker compose ps --format json` reports for each service.
