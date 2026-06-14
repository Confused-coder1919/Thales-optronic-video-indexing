from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.src.system_llm_api import router as system_router
from thales.llm import router as llm_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(system_router)
    return TestClient(app)


def test_off_override_returns_empty_schema():
    llm_router.set_runtime_mode_override("off")
    payload = llm_router.generate_index({"text": "tank observed"})
    assert payload == {"entities": []}
    llm_router.set_runtime_mode_override("env")


def test_set_mistral_mode_without_key_returns_400(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    monkeypatch.setattr(llm_router, "MISTRAL_API_KEY", None)

    client = _client()
    response = client.post("/api/system/llm-mode", json={"mode": "mistral"})

    assert response.status_code == 400
    assert "MISTRAL_API_KEY" in response.text


def test_set_ollama_mode_when_unreachable_returns_400(monkeypatch):
    monkeypatch.setattr(llm_router, "is_ollama_reachable", lambda timeout_seconds=1.5: False)

    client = _client()
    response = client.post("/api/system/llm-mode", json={"mode": "ollama"})

    assert response.status_code == 400
    assert "Ollama" in response.text
