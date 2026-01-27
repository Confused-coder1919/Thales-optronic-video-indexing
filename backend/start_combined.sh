#!/usr/bin/env bash
set -e

DATA_DIR="${ENTITY_INDEXING_DATA_DIR:-/app/data/entity_indexing}"
mkdir -p "$DATA_DIR"

# Start worker in the background
celery -A backend.src.entity_indexing.celery_app.celery_app worker --loglevel=info &

# Start API (foreground)
uvicorn backend.src.entity_api:app --host 0.0.0.0 --port "${PORT:-8000}"
