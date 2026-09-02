"""
Thales - Military Entity Detection Pipeline

A pipeline for processing voice transcripts and videos to detect 
military entities using LLMs and vision models.
"""

__version__ = "1.0.0"
__author__ = "Syed Tashfin"

from thales.config import (
    ENTITY_CATEGORIES,
    ENTITY_NORMALIZATION,
    VALID_CATEGORIES,
)

__all__ = [
    "__version__",
    "ENTITY_CATEGORIES",
    "ENTITY_NORMALIZATION", 
    "VALID_CATEGORIES",
]

