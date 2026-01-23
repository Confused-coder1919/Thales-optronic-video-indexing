from backend.src.entity_indexing.embeddings import cosine_similarity
from backend.src.entity_indexing.search import parse_query


def test_parse_query():
    tokens = parse_query("aircraft, turret , personnel")
    assert tokens == ["aircraft", "turret", "personnel"]


def test_cosine_similarity():
    assert round(cosine_similarity([1, 0], [1, 0]), 5) == 1.0
    assert round(cosine_similarity([1, 0], [0, 1]), 5) == 0.0
