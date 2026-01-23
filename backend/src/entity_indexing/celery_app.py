from __future__ import annotations

from celery import Celery

from .config import REDIS_URL

celery_app = Celery(
    "entity_indexing",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.src.entity_indexing.tasks"],
)

celery_app.conf.update(task_track_started=True)
