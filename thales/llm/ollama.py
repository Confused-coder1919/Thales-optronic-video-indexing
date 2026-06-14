from __future__ import annotations

import json
from typing import Any, Dict
from urllib import error as urlerror
from urllib import request as urlrequest

from thales.llm.base import LLMProvider
from thales.llm.schema import (
    build_index_prompt,
    build_json_repair_prompt,
    parse_json_payload,
)


class OllamaProviderError(RuntimeError):
    """Raised when Ollama generation fails."""


class OllamaProvider(LLMProvider):
    """Ollama-backed provider for structured entity extraction."""

    def __init__(self, base_url: str, model: str, timeout_seconds: int):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _chat(self, prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": 0.1},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlrequest.urlopen(req, timeout=self.timeout_seconds) as response:
                status = response.getcode()
                body = response.read().decode("utf-8", errors="replace")
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").strip()[:500]
            raise OllamaProviderError(
                f"Ollama returned HTTP {exc.code}: {body}"
            ) from exc
        except Exception as exc:
            raise OllamaProviderError(
                f"Ollama request failed at {url}: {type(exc).__name__}: {exc}"
            ) from exc

        if status >= 400:
            snippet = (body or "").strip()[:500]
            raise OllamaProviderError(f"Ollama returned HTTP {status}: {snippet}")

        try:
            data = json.loads(body)
        except Exception as exc:
            raise OllamaProviderError("Ollama returned non-JSON HTTP payload.") from exc

        message = data.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        # Some adapters expose OpenAI-compatible shape.
        choices = data.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

        raise OllamaProviderError("Ollama response missing message content.")

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
                raise OllamaProviderError(
                    "Ollama returned invalid JSON twice (initial + repair)."
                ) from exc
