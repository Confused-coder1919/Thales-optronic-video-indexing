from __future__ import annotations

from typing import Any, Dict

from thales.llm.base import LLMProvider
from thales.llm.schema import (
    build_index_prompt,
    build_json_repair_prompt,
    parse_json_payload,
)


class MistralProvider(LLMProvider):
    """Mistral-backed provider for structured entity extraction."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is required for MistralProvider.")
        try:
            from mistralai import Mistral
        except Exception as exc:  # pragma: no cover - depends on optional runtime install
            raise RuntimeError(
                "mistralai package is required for MistralProvider. "
                "Install dependencies from requirements.txt."
            ) from exc
        self.model = model
        self.client = Mistral(api_key=api_key)

    def _chat(self, prompt: str) -> str:
        response = self.client.chat.complete(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()

    def generate_index(self, segment_input: Dict[str, Any]) -> Dict[str, Any]:
        prompt = build_index_prompt(segment_input)
        raw = self._chat(prompt)
        try:
            return parse_json_payload(raw)
        except Exception:
            repair_prompt = build_json_repair_prompt(raw, segment_input)
            repaired = self._chat(repair_prompt)
            try:
                return parse_json_payload(repaired)
            except Exception as exc:
                raise RuntimeError(
                    "Mistral returned invalid JSON twice (initial + repair)."
                ) from exc
