"""
tests/test_exemplar_rag.py
===========================
Unit tests for app/core/exemplar_rag.py (TASK-003).
"""

import time

from app.core.exemplar_rag import (
    DialogueExemplar,
    ExemplarRAG,
    format_exemplars_for_prompt,
)


def test_init_and_load_default_bank():
    rag = ExemplarRAG()
    assert rag.get_total_count() > 0
    assert rag.get_total_count() == 150


def test_init_with_custom_list():
    custom_data = [
        {
            "id": "c_001",
            "level": "A1",
            "persona": "Alex",
            "topic": "hobbies",
            "dialogue_act": "greeting",
            "text": "Hello, let us play sports!",
            "quality_score": 4.8,
        },
        {
            "id": "c_002",
            "level": "B2",
            "persona": "Oscar",
            "topic": "tech",
            "dialogue_act": "question",
            "text": "What is AI?",
            "quality_score": 5.0,
        },
    ]
    rag = ExemplarRAG(exemplars=custom_data)
    assert rag.get_total_count() == 2


def test_exact_metadata_retrieval():
    rag = ExemplarRAG()
    results = rag.retrieve(
        level="A1",
        persona="Alex",
        topic="daily_life",
        dialogue_act="greeting",
        top_k=2,
    )
    assert len(results) == 2
    for item in results:
        assert isinstance(item, dict)
        assert hasattr(item, "text")
        assert "text" in item
        assert item["level"] == "A1"


def test_retrieval_returns_2_to_3_exemplars():
    rag = ExemplarRAG()
    results_3 = rag.retrieve(level="B1", topic="hobbies", top_k=3)
    assert len(results_3) == 3

    results_2 = rag.retrieve(level="B2", topic="work", top_k=2)
    assert len(results_2) == 2


def test_progressive_relaxation_fallback():
    rag = ExemplarRAG()
    # Query with non-existent persona and topic to trigger relaxation fallback
    results = rag.retrieve(
        level="C1",
        persona="NonExistentPersona",
        topic="QuantumPhysics101",
        dialogue_act="greeting",
        top_k=3,
    )
    assert len(results) == 3
    # Check that it still returned valid exemplars
    assert all("text" in ex and len(ex["text"]) > 0 for ex in results)


def test_semantic_search_scoring():
    rag = ExemplarRAG()
    state_summary = "I love traveling to Europe and exploring ancient cities."
    results = rag.retrieve(
        level="A2",
        topic="travel",
        state_summary=state_summary,
        top_k=3,
        use_mmr=True,
    )
    assert len(results) == 3
    # Check that scores are computed
    assert all("score" in ex and ex["score"] > 0 for ex in results)


def test_mmr_diversity():
    rag = ExemplarRAG()
    state_summary = "Discussing daily routine, coffee, and morning habits."
    no_mmr = rag.retrieve(
        level="A1",
        state_summary=state_summary,
        top_k=3,
        use_mmr=False,
    )
    with_mmr = rag.retrieve(
        level="A1",
        state_summary=state_summary,
        top_k=3,
        use_mmr=True,
    )
    assert len(no_mmr) == 3
    assert len(with_mmr) == 3


def test_dialogue_exemplar_dict_and_attr_access():
    ex = DialogueExemplar({
        "id": "ex_999",
        "level": "B1",
        "text": "Practice makes perfect.",
        "quality_score": 4.9,
    })

    # Dict access
    assert ex["id"] == "ex_999"
    assert ex["level"] == "B1"
    assert ex["text"] == "Practice makes perfect."

    # Attribute access
    assert ex.id == "ex_999"
    assert ex.level == "B1"
    assert ex.text == "Practice makes perfect."


def test_format_exemplars_for_prompt():
    exemplars = [
        {"dialogue_act": "greeting", "text": "Hello world!"},
        {"dialogue_act": "question", "text": "How are you?"},
    ]
    formatted = format_exemplars_for_prompt(exemplars)
    assert '- [greeting]: "Hello world!"' in formatted
    assert '- [question]: "How are you?"' in formatted

    empty_fmt = format_exemplars_for_prompt([])
    assert empty_fmt == "No specific dialogue exemplars retrieved."


def test_empty_bank_edge_case():
    rag = ExemplarRAG(exemplars=[])
    assert rag.get_total_count() == 0
    results = rag.retrieve(level="A1", top_k=3)
    assert results == []


def test_retrieval_latency_benchmark():
    rag = ExemplarRAG()
    start_time = time.perf_counter()
    for _ in range(20):
        rag.retrieve(
            level="B1",
            persona="Chanel",
            topic="hobbies",
            dialogue_act="question",
            state_summary="Talking about movies and leisure time",
            top_k=3,
        )
    elapsed_ms = (time.perf_counter() - start_time) / 20 * 1000
    assert elapsed_ms < 15.0  # Must be faster than 15ms per retrieval
