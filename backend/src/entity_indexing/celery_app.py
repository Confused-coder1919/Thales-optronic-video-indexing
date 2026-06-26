from __future__ import annotations

import os

from celery import Celery

from .config import REDIS_URL

celery_app = Celery(
    "entity_indexing",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.src.entity_indexing.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=int(
        os.getenv("ENTITY_INDEXING_WORKER_PREFETCH_MULTIPLIER", "1")
    ),
    worker_concurrency=int(os.getenv("ENTITY_INDEXING_WORKER_CONCURRENCY", "1")),
)
