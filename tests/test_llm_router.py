from __future__ import annotations

import pytest

from thales.llm import router


def test_auto_mode_uses_ollama_when_mistral_key_missing(monkeypatch):
    calls = {"ollama": 0}

    class FakeOllama:
        def __init__(self, base_url: str, model: str, timeout_seconds: int):
            pass

        def generate_index(self, segment_input):
            calls["ollama"] += 1
            return {"entities": ["military truck"]}

    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr(router, "OllamaProvider", FakeOllama)
    monkeypatch.setattr(router, "is_ollama_reachable", lambda timeout_seconds=1.5: True)

    payload = router.generate_index({"text": "truck"})
    assert payload["entities"] == ["military truck"]
    assert calls["ollama"] == 1


def test_auto_mode_falls_back_to_ollama_after_transient_mistral(monkeypatch):
    calls = {"mistral": 0, "ollama": 0}

    class FakeMistral:
        def __init__(self, api_key: str, model: str):
            pass

        def generate_index(self, segment_input):
            calls["mistral"] += 1
            raise TimeoutError("request timed out")

    class FakeOllama:
        def __init__(self, base_url: str, model: str, timeout_seconds: int):
            pass

        def generate_index(self, segment_input):
            calls["ollama"] += 1
            return {"entities": ["drone"]}

    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy-key")
    monkeypatch.setattr(router, "MistralProvider", FakeMistral)
    monkeypatch.setattr(router, "OllamaProvider", FakeOllama)
    monkeypatch.setattr(router.time, "sleep", lambda _: None)

    payload = router.generate_index({"text": "uav"})
    assert payload == {"entities": ["drone"]}
    assert calls["mistral"] == 3  # initial + 2 retries
    assert calls["ollama"] == 1


def test_forced_mistral_does_not_fallback_to_ollama(monkeypatch):
    calls = {"ollama": 0}

    class FakeMistral:
        def __init__(self, api_key: str, model: str):
            pass

        def generate_index(self, segment_input):
            raise RuntimeError("hard failure")

    class FakeOllama:
        def __init__(self, base_url: str, model: str, timeout_seconds: int):
            calls["ollama"] += 1

        def generate_index(self, segment_input):
            return {"entities": ["ignored"]}

    monkeypatch.setenv("LLM_PROVIDER", "mistral")
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy-key")
    monkeypatch.setattr(router, "MistralProvider", FakeMistral)
    monkeypatch.setattr(router, "OllamaProvider", FakeOllama)

    with pytest.raises(RuntimeError, match="hard failure"):
        router.generate_index({"text": "tank"})

    assert calls["ollama"] == 0


def test_env_auto_returns_empty_when_no_provider_available(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "auto")
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr(router, "is_ollama_reachable", lambda timeout_seconds=1.5: False)

    payload = router.generate_index({"text": "tank"})
    assert payload == {"entities": []}
