from backend.src.entity_indexing.embeddings import cosine_similarity
from backend.src.entity_indexing.search import merge_search_entities, parse_query


def test_parse_query():
    tokens = parse_query("aircraft, turret , personnel")
    assert tokens == ["aircraft", "turret", "personnel"]


def test_cosine_similarity():
    assert round(cosine_similarity([1, 0], [1, 0]), 5) == 1.0
    assert round(cosine_similarity([1, 0], [0, 1]), 5) == 0.0


def test_merge_search_entities_includes_transcript_mentions():
    entities = merge_search_entities(
        {
            "truck": {
                "count": 3,
                "presence": 0.25,
                "sources": ["yolo"],
            }
        },
        {
            "missile": {
                "count": 2,
                "presence": 0.1,
                "sources": ["transcript"],
            }
        },
    )

    assert sorted(entities.keys()) == ["missile", "truck"]
    assert entities["missile"]["sources"] == ["transcript"]
