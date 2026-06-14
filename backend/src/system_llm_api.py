from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from thales.llm.router import get_llm_status, set_runtime_mode_override

router = APIRouter(prefix="/api/system", tags=["system"])


class LLMModeRequest(BaseModel):
    mode: Literal["env", "auto", "mistral", "ollama", "off"]


@router.get("/llm-status")
def llm_status() -> dict:
    return get_llm_status()


@router.post("/llm-mode")
def llm_mode(payload: LLMModeRequest) -> dict:
    requested = payload.mode
    preview = get_llm_status(requested)

    if requested == "mistral" and not preview["mistral_available"]:
        raise HTTPException(status_code=400, detail="Mistral mode requires MISTRAL_API_KEY.")

    if requested == "ollama" and not preview["ollama_reachable"]:
        raise HTTPException(
            status_code=400,
            detail=(
                "Ollama mode selected but Ollama is not reachable. "
                "Start Ollama (docker-compose.ollama.yml)."
            ),
        )

    try:
        set_runtime_mode_override(requested)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return get_llm_status()
