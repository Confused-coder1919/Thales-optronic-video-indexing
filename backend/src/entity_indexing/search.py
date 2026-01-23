from __future__ import annotations

from typing import Dict, List, Tuple

from .embeddings import EmbeddingProvider, cosine_similarity, load_label_index


def parse_query(q: str) -> List[str]:
    tokens = [token.strip().lower() for token in q.split(",") if token.strip()]
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
