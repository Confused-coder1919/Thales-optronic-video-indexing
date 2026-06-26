from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Tuple
from urllib import error as urlerror
from urllib import request as urlrequest

from thales.config import (
    LLM_PROVIDER,
    LLM_TIMEOUT_SECONDS,
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from thales.llm.base import LLMProvider
from thales.llm.mistral import MistralProvider
from thales.llm.ollama import OllamaProvider

logger = logging.getLogger(__name__)

_ALLOWED_ENV_MODES = {"auto", "mistral", "ollama"}
_ALLOWED_RUNTIME_MODES = {"env", "auto", "mistral", "ollama", "off"}
_RUNTIME_MODE_OVERRIDE = "env"


def _provider_mode() -> str:
    mode = os.getenv("LLM_PROVIDER", LLM_PROVIDER).strip().lower()
    if mode not in _ALLOWED_ENV_MODES:
        return "auto"
    return mode


def _timeout_seconds() -> int:
    value = os.getenv("LLM_TIMEOUT_SECONDS", str(LLM_TIMEOUT_SECONDS)).strip()
    try:
        return max(1, int(value))
    except ValueError:
        return LLM_TIMEOUT_SECONDS


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
    transient_markers = [
        "429",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "rate limit",
        "too many requests",
        "connection reset",
        "connection aborted",
        "service unavailable",
        "bad gateway",
        "gateway timeout",
    ]
    return any(marker in text for marker in transient_markers)


def _build_mistral_provider() -> LLMProvider:
    api_key = os.getenv("MISTRAL_API_KEY", MISTRAL_API_KEY or "").strip()
    model = os.getenv("MISTRAL_MODEL", MISTRAL_MODEL).strip() or MISTRAL_MODEL
    return MistralProvider(api_key=api_key, model=model)


def _ollama_settings() -> Tuple[str, str]:
    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL).strip() or OLLAMA_BASE_URL
    model = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL).strip() or OLLAMA_MODEL
    return base_url, model


def _build_ollama_provider() -> LLMProvider:
    base_url, model = _ollama_settings()
    return OllamaProvider(
        base_url=base_url,
        model=model,
        timeout_seconds=_timeout_seconds(),
    )


def _call_with_retries(provider: LLMProvider, segment_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retry transient failures up to 2 times (3 attempts total).
    """
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                logger.info(
                    "Retrying provider call (%s/%s)...",
                    attempt,
                    max_retries,
                )
            return provider.generate_index(segment_input)
        except Exception as exc:
            if attempt >= max_retries or not _is_transient_error(exc):
                raise
            delay = 2 ** attempt
            logger.info(
                "Transient LLM error (%s). Backing off for %ss before retry.",
                type(exc).__name__,
                delay,
            )
            time.sleep(delay)
    raise RuntimeError("Unreachable retry branch.")


def _mistral_available() -> bool:
    return bool(os.getenv("MISTRAL_API_KEY", MISTRAL_API_KEY or "").strip())


def is_ollama_reachable(timeout_seconds: float = 1.5) -> bool:
    base_url, _ = _ollama_settings()
    if not base_url:
        return False

    url = f"{base_url.rstrip('/')}/api/tags"
    req = urlrequest.Request(url, method="GET")
    try:
        with urlrequest.urlopen(req, timeout=timeout_seconds) as response:
            code = response.getcode()
            if code >= 400:
                return False
            body = response.read().decode("utf-8", errors="replace").strip()
            if not body:
                return False
            json.loads(body)
            return True
    except urlerror.HTTPError:
        return False
    except Exception:
        return False


def get_runtime_mode_override() -> str:
    return _RUNTIME_MODE_OVERRIDE


def set_runtime_mode_override(mode: str) -> str:
    global _RUNTIME_MODE_OVERRIDE
    normalized = (mode or "").strip().lower()
    if normalized not in _ALLOWED_RUNTIME_MODES:
        raise ValueError("Invalid mode. Use env|auto|mistral|ollama|off.")
    _RUNTIME_MODE_OVERRIDE = normalized
    logger.info("LLM runtime mode override set to: %s", normalized)
    return normalized


def _policy_mode(runtime_mode: str) -> str:
    return _provider_mode() if runtime_mode == "env" else runtime_mode


def _resolve_effective_mode(runtime_mode: str) -> Tuple[str, str]:
    policy = _policy_mode(runtime_mode)
    has_mistral = _mistral_available()
    ollama_ok = is_ollama_reachable()
    base_url, _ = _ollama_settings()

    if policy == "off":
        return "off", "LLM extraction disabled by runtime override."

    if policy == "mistral":
        if has_mistral:
            return "mistral", "Cloud mode selected (Mistral API key detected)."
        return "off", "Mistral mode selected but MISTRAL_API_KEY is not set."

    if policy == "ollama":
        if ollama_ok:
            return "ollama", "Local mode selected (Ollama reachable)."
        return "off", f"Local mode selected but Ollama is not reachable at {base_url}."

    if policy == "auto":
        if has_mistral:
            return "mistral", "Auto mode selected Mistral (key available)."
        if ollama_ok:
            return "ollama", "Auto mode selected Ollama (Mistral key missing)."
        return "off", "Auto mode has no available provider (missing Mistral key and Ollama unreachable)."

    return "off", "Unsupported mode configuration."


def get_llm_status(runtime_mode: str | None = None) -> Dict[str, Any]:
    mode = get_runtime_mode_override() if runtime_mode is None else runtime_mode
    effective_mode, note = _resolve_effective_mode(mode)
    base_url, model = _ollama_settings()

    return {
        "mode": mode,
        "effective_mode": effective_mode,
        "mistral_available": _mistral_available(),
        "ollama_reachable": is_ollama_reachable(),
        "ollama_base_url": base_url or None,
        "ollama_model": model or None,
        "note": note,
    }


def _generate_env_mode(segment_input: Dict[str, Any]) -> Dict[str, Any]:
    mode = _provider_mode()
    logger.info("LLM provider selected from environment: %s", mode)

    if mode == "ollama":
        logger.info("Using Ollama provider (env forced).")
        return _build_ollama_provider().generate_index(segment_input)

    if mode == "mistral":
        logger.info("Using Mistral provider (env forced).")
        return _call_with_retries(_build_mistral_provider(), segment_input)

    if not _mistral_available():
        if not is_ollama_reachable():
            logger.info(
                "Env auto mode: no Mistral key and Ollama is unreachable; returning empty schema."
            )
            return {"entities": []}
        logger.info("Env auto mode: MISTRAL_API_KEY missing; falling back to Ollama.")
        return _build_ollama_provider().generate_index(segment_input)

    try:
        logger.info("Env auto mode: trying Mistral first.")
        return _call_with_retries(_build_mistral_provider(), segment_input)
    except Exception as mistral_exc:
        if not _is_transient_error(mistral_exc):
            raise
        logger.info(
            "Env auto mode: Mistral transient failure (%s), falling back to Ollama.",
            type(mistral_exc).__name__,
        )
        try:
            return _build_ollama_provider().generate_index(segment_input)
        except Exception as ollama_exc:
            raise RuntimeError(
                "Mistral failed and Ollama fallback failed. "
                "Set LLM_PROVIDER or check backend availability."
            ) from ollama_exc


def _generate_override_mode(segment_input: Dict[str, Any], mode: str) -> Dict[str, Any]:
    policy = _policy_mode(mode)
    logger.info("LLM override mode selected: %s (policy=%s)", mode, policy)

    if policy == "off":
        logger.info("LLM provider decision: off (deterministic empty entities).")
        return {"entities": []}

    if policy == "mistral":
        if not _mistral_available():
            raise ValueError("Mistral mode requires MISTRAL_API_KEY.")
        logger.info("LLM provider decision: mistral (override policy).")
        return _call_with_retries(_build_mistral_provider(), segment_input)

    if policy == "ollama":
        if not is_ollama_reachable():
            raise ValueError("Ollama mode selected but Ollama is not reachable.")
        logger.info("LLM provider decision: ollama (override policy).")
        return _build_ollama_provider().generate_index(segment_input)

    if policy == "auto":
        if _mistral_available():
            logger.info("LLM provider decision: mistral (auto override, key available).")
            try:
                return _call_with_retries(_build_mistral_provider(), segment_input)
            except Exception as mistral_exc:
                if not _is_transient_error(mistral_exc):
                    raise
                if not is_ollama_reachable():
                    logger.info(
                        "LLM provider fallback unavailable after mistral transient failure; returning off."
                    )
                    return {"entities": []}
                logger.info(
                    "LLM provider fallback triggered: mistral->ollama due to %s.",
                    type(mistral_exc).__name__,
                )
                return _build_ollama_provider().generate_index(segment_input)

        if is_ollama_reachable():
            logger.info("LLM provider decision: ollama (auto override, no Mistral key).")
            return _build_ollama_provider().generate_index(segment_input)

        logger.info("LLM provider decision: off (auto override, no providers available).")
        return {"entities": []}

    raise ValueError("Invalid mode. Use env|auto|mistral|ollama|off.")


def generate_index(segment_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route indexing call to configured provider with runtime override support.
    """
    mode = get_runtime_mode_override()
    if mode == "env":
        return _generate_env_mode(segment_input)
    return _generate_override_mode(segment_input, mode)
