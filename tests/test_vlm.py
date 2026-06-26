from __future__ import annotations

import pytest

from thales import vlm


def test_auto_vision_uses_ollama_when_mistral_missing(monkeypatch):
    client = vlm.VisionClient()
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr(vlm, "MISTRAL_API_KEY", None)
    monkeypatch.setattr(vlm, "is_ollama_vision_reachable", lambda timeout_seconds=1.5: True)
    monkeypatch.setattr(
        client,
        "_complete_ollama",
        lambda prompt, image_base64, temperature: "local vision ok",
    )

    result = client.complete("describe", "abc123", temperature=0.1)
    assert result == "local vision ok"


def test_auto_vision_raises_when_no_backend_available(monkeypatch):
    client = vlm.VisionClient()
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr(vlm, "MISTRAL_API_KEY", None)
    monkeypatch.setattr(vlm, "is_ollama_vision_reachable", lambda timeout_seconds=1.5: False)

    with pytest.raises(vlm.VisionBackendError, match="No vision backend available"):
        client.complete("describe", "abc123", temperature=0.1)
