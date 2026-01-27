"""
Compatibility entrypoint for uvicorn.

This module re-exports the FastAPI app from backend.src.entity_api so
existing commands targeting backend.main:app continue to work.
"""

from backend.src.entity_api import app  # noqa: F401
