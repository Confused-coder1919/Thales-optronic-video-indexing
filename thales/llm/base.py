from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class LLMProvider(ABC):
    """Provider contract for indexed JSON generation."""

    @abstractmethod
    def generate_index(self, segment_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured index output for a segment input payload.
        """
        raise NotImplementedError

