from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from .config import VERIFY_MODEL, VERIFY_THRESHOLD


class ClipVerifier:
    def __init__(self, labels: List[str], threshold: float = VERIFY_THRESHOLD) -> None:
        self.labels = [label for label in labels if label]
        self.threshold = threshold
        self._model = None
        self._processor = None
        self._text_features = None

    def _ensure_model(self) -> None:
        if self._model is not None:
            return
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._model = CLIPModel.from_pretrained(VERIFY_MODEL).to(device)
        self._processor = CLIPProcessor.from_pretrained(VERIFY_MODEL)
        if not self.labels:
            return
        with torch.no_grad():
            inputs = self._processor(
                text=[f"a photo of {label}" for label in self.labels],
                return_tensors="pt",
                padding=True,
            ).to(device)
            text_features = self._model.get_text_features(**inputs)
            if not isinstance(text_features, torch.Tensor):
                pooled = getattr(text_features, "pooler_output", None)
                if pooled is None:
                    pooled = getattr(text_features, "text_embeds", None)
                text_features = pooled
            if text_features is None:
                return
            self._text_features = torch.nn.functional.normalize(text_features, p=2, dim=1)

    def verify(self, frame_path: Path) -> List[Dict]:
        if not self.labels:
            return []
        self._ensure_model()
        if self._text_features is None:
            return []
        device = self._model.device
        image = Image.open(frame_path).convert("RGB")
        inputs = self._processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            image_features = self._model.get_image_features(**inputs)
            if not isinstance(image_features, torch.Tensor):
                pooled = getattr(image_features, "pooler_output", None)
                if pooled is None:
                    pooled = getattr(image_features, "image_embeds", None)
                image_features = pooled
            if image_features is None:
                return []
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
                        "source": "verify",
                    }
                )
        return detections
