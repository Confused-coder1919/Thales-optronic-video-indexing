#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from thales.llm.router import generate_index
from thales.llm.schema import validate_index_payload


def _sample_segment() -> Dict[str, object]:
    return {
        "text": (
            "At 00:30 a military truck moves near a trailer while two soldiers "
            "stand beside an armored vehicle."
        ),
        "timestamps": {"start": "00:30", "end": "00:40"},
        "vision_detections": [
            {"timestamp": "00:30", "labels": ["truck", "trailer", "person"]},
            {"timestamp": "00:35", "labels": ["tank", "person"]},
        ],
    }


def _run_mode(mode: str) -> Dict[str, object]:
    os.environ["LLM_PROVIDER"] = mode
    payload = generate_index(_sample_segment())
    return validate_index_payload(payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test for LLM backends (Ollama and Mistral)."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return non-zero if any checked mode fails.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and print planned calls without network requests.",
    )
    args = parser.parse_args()

    failures: List[Tuple[str, str]] = []

    if args.dry_run:
        print("== DRY RUN ==")
        print("No network calls will be performed.")
        print("Planned mode checks: ollama, mistral (if MISTRAL_API_KEY is set).")
        print(f"LLM_PROVIDER env (current): {os.getenv('LLM_PROVIDER', '(unset)')}")
        print(f"OLLAMA_BASE_URL env (current): {os.getenv('OLLAMA_BASE_URL', '(unset)')}")
        print(f"OLLAMA_MODEL env (current): {os.getenv('OLLAMA_MODEL', '(unset)')}")
        mistral_key = os.getenv("MISTRAL_API_KEY", "").strip()
        if mistral_key:
            print("Mistral key detected: yes")
        else:
            print("Mistral key detected: no (mistral mode would be skipped)")
        # Validate schema helper on a minimal payload without calling providers.
        payload = validate_index_payload({"entities": ["military truck"]})
        print(f"Schema validator OK: {payload}")
        return 0

    print("== Ollama mode ==")
    try:
        ollama_payload = _run_mode("ollama")
        print(f"Ollama OK: {ollama_payload}")
    except Exception as exc:
        failures.append(("ollama", f"{type(exc).__name__}: {exc}"))
        print(f"Ollama FAIL: {type(exc).__name__}: {exc}")

    mistral_key = os.getenv("MISTRAL_API_KEY", "").strip()
    if mistral_key:
        print("== Mistral mode ==")
        try:
            mistral_payload = _run_mode("mistral")
            print(f"Mistral OK: {mistral_payload}")
        except Exception as exc:
            failures.append(("mistral", f"{type(exc).__name__}: {exc}"))
            print(f"Mistral FAIL: {type(exc).__name__}: {exc}")
    else:
        print("== Mistral mode ==")
        print("Skipped: MISTRAL_API_KEY is not set.")

    if failures:
        print("\nSmoke summary:")
        for mode, err in failures:
            print(f"- {mode}: {err}")
        return 1 if args.strict else 0

    print("\nSmoke summary: all checked modes succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
