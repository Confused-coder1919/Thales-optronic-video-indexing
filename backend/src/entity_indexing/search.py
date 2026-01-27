from __future__ import annotations

from typing import Dict, List, Tuple
import re

from .embeddings import EmbeddingProvider, cosine_similarity, load_label_index


def parse_query(q: str) -> List[str]:
    parts = [part.strip().lower() for part in q.split(",") if part.strip()]
    tokens: List[str] = []

    def add_token(token: str) -> None:
        token = token.strip().lower()
        if not token:
            return
        if token not in tokens:
            tokens.append(token)
        # basic singularization for plural forms
        if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
            singular = token[:-1]
            if singular and singular not in tokens:
                tokens.append(singular)

    for part in parts:
        add_token(part)
        for word in re.split(r"\s+", part):
            add_token(word)

    return tokens


def find_similar_entities(
    query: str, similarity: float, provider: EmbeddingProvider
) -> List[Tuple[str, float]]:
    labels = load_label_index()
    if not labels:
        return []
    query_vec = provider.encode([query])[0]
    scored = []
    for label, vec in labels.items():
        score = cosine_similarity(query_vec, vec)
        if score >= similarity:
            scored.append((label, score))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored
