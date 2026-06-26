from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

from thales.config import (
    LLM_TIMEOUT_SECONDS,
    MISTRAL_API_KEY,
    OLLAMA_BASE_URL,
    OLLAMA_VISION_MODEL,
    PIXTRAL_MODEL,
    VISION_PROVIDER,
)

logger = logging.getLogger(__name__)

_ALLOWED_VISION_MODES = {"auto", "mistral", "ollama"}


def _vision_mode() -> str:
    mode = os.getenv("VISION_PROVIDER", VISION_PROVIDER).strip().lower()
    if mode not in _ALLOWED_VISION_MODES:
        return "auto"
    return mode


def _timeout_seconds() -> int:
    value = os.getenv("LLM_TIMEOUT_SECONDS", str(LLM_TIMEOUT_SECONDS)).strip()
    try:
        return max(1, int(value))
    except ValueError:
        return LLM_TIMEOUT_SECONDS


def _mistral_key() -> str:
    return os.getenv("MISTRAL_API_KEY", MISTRAL_API_KEY or "").strip()


def _ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL).strip() or OLLAMA_BASE_URL


def _ollama_vision_model() -> str:
    model = os.getenv("OLLAMA_VISION_MODEL", OLLAMA_VISION_MODEL).strip()
    return model or OLLAMA_VISION_MODEL


def is_ollama_vision_reachable(timeout_seconds: float = 1.5) -> bool:
    url = f"{_ollama_base_url().rstrip('/')}/api/tags"
    req = urlrequest.Request(url, method="GET")
    try:
        with urlrequest.urlopen(req, timeout=timeout_seconds) as response:
            if response.getcode() >= 400:
                return False
            json.loads(response.read().decode("utf-8", errors="replace"))
            return True
    except Exception:
        return False


def _status_code_from_exception(exc: Exception) -> int | None:
    for attr in ("status_code", "http_status", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
        try:
            if value is not None:
                return int(value)
        except Exception:
            continue
    return None


def _is_transient_error(exc: Exception) -> bool:
    status = _status_code_from_exception(exc)
    if status == 429:
        return True
    if status is not None and 500 <= status <= 599:
        return True

    text = str(exc).lower()
    markers = [
        "429",
        "timeout",
        "timed out",
        "too many requests",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
        "connection reset",
        "temporarily unavailable",
    ]
    return any(marker in text for marker in markers)


class VisionBackendError(RuntimeError):
    """Raised when no configured vision backend can complete the request."""


class VisionClient:
    def __init__(self) -> None:
        self.mode = _vision_mode()
        self.timeout_seconds = _timeout_seconds()
        self._mistral_client = None

    def _ensure_mistral_client(self):
        api_key = _mistral_key()
        if not api_key:
            raise VisionBackendError("MISTRAL_API_KEY is not set for vision requests.")
        if self._mistral_client is None:
            try:
                from mistralai import Mistral
            except Exception as exc:
                raise VisionBackendError(
                    "mistralai package is required for Mistral/Pixtral vision requests."
                ) from exc
            self._mistral_client = Mistral(api_key=api_key)
        return self._mistral_client

    def _complete_mistral(self, prompt: str, image_base64: str, temperature: float) -> str:
        client = self._ensure_mistral_client()
        response = client.chat.complete(
            model=PIXTRAL_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{image_base64}",
                        },
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content.strip()

    def _complete_ollama(self, prompt: str, image_base64: str, temperature: float) -> str:
        payload = {
            "model": _ollama_vision_model(),
            "messages": [{"role": "user", "content": prompt, "images": [image_base64]}],
            "stream": False,
            "options": {"temperature": temperature},
        }
        req = urlrequest.Request(
            f"{_ollama_base_url().rstrip('/')}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlrequest.urlopen(req, timeout=self.timeout_seconds) as response:
                status = response.getcode()
                body = response.read().decode("utf-8", errors="replace")
        except urlerror.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace").strip()[:500]
            raise VisionBackendError(f"Ollama vision returned HTTP {exc.code}: {body}") from exc
        except Exception as exc:
            raise VisionBackendError(
                f"Ollama vision request failed at {_ollama_base_url()}: {type(exc).__name__}: {exc}"
            ) from exc

        if status >= 400:
            raise VisionBackendError(f"Ollama vision returned HTTP {status}: {body[:500]}")

        try:
            data: Any = json.loads(body)
        except Exception as exc:
            raise VisionBackendError("Ollama vision returned non-JSON HTTP payload.") from exc

        message = data.get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        choices = data.get("choices") or []
        if choices:
            choice_message = choices[0].get("message") or {}
            content = choice_message.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()

        raise VisionBackendError("Ollama vision response missing message content.")

    def complete(self, prompt: str, image_base64: str, temperature: float = 0.1) -> str:
        if self.mode == "mistral":
            logger.info("Vision provider selected: mistral")
            return self._complete_mistral(prompt, image_base64, temperature)

        if self.mode == "ollama":
            if not is_ollama_vision_reachable():
                raise VisionBackendError("Ollama vision backend is not reachable.")
            logger.info("Vision provider selected: ollama")
            return self._complete_ollama(prompt, image_base64, temperature)

        if _mistral_key():
            logger.info("Vision provider selected: mistral (auto)")
            try:
                return self._complete_mistral(prompt, image_base64, temperature)
            except Exception as exc:
                if not _is_transient_error(exc):
                    raise
                if not is_ollama_vision_reachable():
                    raise VisionBackendError(
                        "Mistral vision failed and Ollama vision is not reachable."
                    ) from exc
                logger.info("Vision fallback triggered: mistral->ollama")
                return self._complete_ollama(prompt, image_base64, temperature)

        if is_ollama_vision_reachable():
            logger.info("Vision provider selected: ollama (auto)")
            return self._complete_ollama(prompt, image_base64, temperature)

        raise VisionBackendError(
            "No vision backend available. Configure MISTRAL_API_KEY or run Ollama with a vision model."
        )


def get_vision_client() -> VisionClient:
    return VisionClient()
