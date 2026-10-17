# Deployment

## Environments

- **dev** — Docker Compose, hot reload
- **test** — CI pipeline, ephemeral
- **prod** — Docker, Gunicorn, WhiteNoise, Sentry

## Quick Start (dev)

```bash
docker compose up -d --build
```

Backend: http://localhost:8000
Frontend: http://localhost:3000
API Docs: http://localhost:8000/api/docs/

## Migrations

```bash
docker compose run --rm backend python manage.py makemigrations
docker compose run --rm backend python manage.py migrate
```

## Backup

```bash
./deploy/backup.sh
```

## Restore

```bash
./deploy/restore.sh backup_file.sql
```

## Health Check

GET /api/v1/health/
