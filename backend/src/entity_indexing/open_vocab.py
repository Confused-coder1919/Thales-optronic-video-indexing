from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from .config import OPEN_VOCAB_LABELS, OPEN_VOCAB_MODEL, OPEN_VOCAB_THRESHOLD


class OpenVocabClassifier:
    def __init__(self) -> None:
        self.labels = OPEN_VOCAB_LABELS
        self.threshold = OPEN_VOCAB_THRESHOLD
        self._model = None
        self._processor = None
        self._text_features = None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = CLIPModel.from_pretrained(OPEN_VOCAB_MODEL).to(device)
        self._processor = CLIPProcessor.from_pretrained(OPEN_VOCAB_MODEL)
        with torch.no_grad():
            inputs = self._processor(
                text=[f"a photo of {label}" for label in self.labels],
                return_tensors="pt",
                padding=True,
            ).to(device)
            text_features = self._model.get_text_features(**inputs)
            self._text_features = torch.nn.functional.normalize(text_features, p=2, dim=1)

    def detect(self, frame_path: Path) -> List[Dict]:
        if not self.labels:
            return []
        self._ensure_model()
        device = self._model.device
        image = Image.open(frame_path).convert("RGB")
        inputs = self._processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            image_features = self._model.get_image_features(**inputs)
            image_features = torch.nn.functional.normalize(image_features, p=2, dim=1)
            similarity = (image_features @ self._text_features.T).squeeze(0)
        detections: List[Dict] = []
        for idx, score in enumerate(similarity.tolist()):
            if score >= self.threshold:
                detections.append(
                    {
                        "label": self.labels[idx],
                        "confidence": round(float(score), 4),
                        "bbox": [],
                        "source": "clip",
                    }
                )
        return detections
