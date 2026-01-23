from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import numpy as np

from .config import EMBEDDING_MODEL, INDEX_DIR


class EmbeddingProvider:
    def __init__(self) -> None:
        self.model_name = EMBEDDING_MODEL
        self._model = None
        self._tokenizer = None

    def _ensure_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            return
        except Exception:
            from transformers import AutoModel, AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModel.from_pretrained(self.model_name)

    def encode(self, texts: List[str]) -> List[List[float]]:
        self._ensure_model()
        if hasattr(self._model, "encode"):
            vectors = self._model.encode(texts, normalize_embeddings=True)
            return [vec.tolist() for vec in vectors]
        # fallback transformer mean pooling
        import torch

        tokens = self._tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            outputs = self._model(**tokens)
        embeddings = outputs.last_hidden_state
        attention_mask = tokens["attention_mask"].unsqueeze(-1)
        masked = embeddings * attention_mask
        summed = masked.sum(dim=1)
        counts = attention_mask.sum(dim=1)
        mean = summed / counts
        normalized = torch.nn.functional.normalize(mean, p=2, dim=1)
        return [vec.tolist() for vec in normalized]


def index_path() -> Path:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    return INDEX_DIR / "labels.json"


def load_label_index() -> Dict[str, List[float]]:
    path = index_path()
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {item["label"]: item["embedding"] for item in data.get("labels", [])}


def save_label_index(labels: Dict[str, List[float]]) -> None:
    payload = {
        "labels": [
            {"label": label, "embedding": embedding}
            for label, embedding in sorted(labels.items())
        ]
    }
    index_path().write_text(json.dumps(payload, indent=2), encoding="utf-8")


def update_label_index(new_labels: List[str], provider: EmbeddingProvider) -> Dict[str, List[float]]:
    labels = load_label_index()
    missing = [label for label in new_labels if label not in labels]
    if missing:
        vectors = provider.encode(missing)
        for label, vec in zip(missing, vectors):
            labels[label] = vec
        save_label_index(labels)
    return labels


def cosine_similarity(a: List[float], b: List[float]) -> float:
    va = np.array(a)
    vb = np.array(b)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1.0
    return float(np.dot(va, vb) / denom)
