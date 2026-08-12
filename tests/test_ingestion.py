"""
Unit & Ingestion integration tests for TASK-001 / TASK-002:
Data Ingestion Verification, Embeddings Generation & Retrieval Queries
"""

import sqlite3
from pathlib import Path

import pytest

from scripts import generate_embeddings, insert_turso


@pytest.fixture
def temp_db_path(tmp_path):
    db_file = tmp_path / "test_ingestion.db"
    conn = sqlite3.connect(str(db_file))
    conn.executescript(insert_turso.SCHEMA_SQL)
    conn.close()
    return str(db_file)


@pytest.fixture
def sample_yaml_file(tmp_path):
    yaml_content = """
content_unit:
  template_type: band_ladder
  title: "Test IELTS Speaking Topic"
  topic_tags: ["hometown", "travel"]
  target_band_min: 5.0
  target_band_max: 8.0
  register: casual
  source_citation: "Unit Test Book"

band_tiers:
  - band_min: 5.5
    band_max: 6.5
    can_do_description: "Can describe hometown in simple terms"
    grammar_required: ["present simple", "past simple"]
    vocabulary_core: ["hometown", "suburb"]

sample_dialogues:
  - band_level: 6.0
    turn_type: standalone
    function_tag: describe_place
    ai_line: "Where is your hometown located?"
    user_model_answer: "My hometown is located in the northern part of Vietnam."
  - band_level: 7.5
    turn_type: standalone
    function_tag: describe_place
    ai_line: "What do you like most about your hometown?"
    user_model_answer: "What I find most appealing about my hometown is its rich cultural heritage and vibrant street life."

hook_bank:
  - topic_tags: ["hometown"]
    text: "Speaking of hometowns..."
    type: hook

vocabulary_lookup:
  - category: "describing_places"
    tier: "C1"
    terms: ["bustling metropolis", "picturesque scenery"]
"""
    file_path = tmp_path / "test_sample.yaml"
    file_path.write_text(yaml_content, encoding="utf-8")
    return file_path


def test_yaml_ingestion_records(temp_db_path, sample_yaml_file):
    """Test inserting YAML content into SQLite database via insert_turso."""
    conn = insert_turso.get_conn_sqlite(temp_db_path)
    total, n_docs = insert_turso.process_file(Path(sample_yaml_file), conn, dry_run=False, is_turso=False)
    conn.close()

    assert n_docs == 1
    assert total["content_units"] == 1
    assert total["band_tiers"] == 1
    assert total["sample_dialogues"] == 2

    # Verify rows in DB
    conn = sqlite3.connect(temp_db_path)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM content_units")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT COUNT(*) FROM band_tiers")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT COUNT(*) FROM sample_dialogues")
    assert cur.fetchone()[0] == 2

    cur.execute("SELECT COUNT(*) FROM hook_bank")
    assert cur.fetchone()[0] == 1

    cur.execute("SELECT COUNT(*) FROM vocabulary_lookup")
    assert cur.fetchone()[0] == 1

    conn.close()


def test_embeddings_generation(temp_db_path, sample_yaml_file):
    """Test generating embeddings for sample dialogues in SQLite database."""
    conn = insert_turso.get_conn_sqlite(temp_db_path)
    insert_turso.process_file(Path(sample_yaml_file), conn, dry_run=False, is_turso=False)
    conn.close()

    db_adapter = generate_embeddings.SqliteAdapter(temp_db_path)
    rows = db_adapter.fetch_null_embeddings(limit=None)
    assert len(rows) == 2

    # Generate embeddings using local sentence-transformers model
    texts = [generate_embeddings.build_embed_text(r) for r in rows]
    vecs = generate_embeddings.embed_local(texts)
    assert len(vecs) == 2
    assert len(vecs[0]) == 384

    for row, vec in zip(rows, vecs):
        blob = generate_embeddings.floats_to_blob(vec)
        assert len(blob) == 384 * 4  # 384 float32 values = 1536 bytes
        db_adapter.update_embedding(row["id"], blob)

    db_adapter.commit()
    db_adapter.close()

    # Confirm 0 null embeddings remain
    db_adapter2 = generate_embeddings.SqliteAdapter(temp_db_path)
    remaining_nulls = db_adapter2.fetch_null_embeddings(limit=None)
    db_adapter2.close()
    assert len(remaining_nulls) == 0


def test_retrieval_query_simulation(temp_db_path, sample_yaml_file):
    """Test simulating retrieval query filtering by topic and band level."""
    conn = insert_turso.get_conn_sqlite(temp_db_path)
    insert_turso.process_file(Path(sample_yaml_file), conn, dry_run=False, is_turso=False)

    # Insert dummy embedding for testing
    dummy_vec = [0.1] * 384
    blob = generate_embeddings.floats_to_blob(dummy_vec)
    conn.execute("UPDATE sample_dialogues SET embedding = ?", (blob,))
    conn.commit()

    cur = conn.cursor()
    query = """
        SELECT sd.id, sd.ai_line, sd.user_model_answer, sd.band_level
        FROM sample_dialogues sd
        JOIN content_units cu ON sd.content_unit_id = cu.id
        WHERE cu.topic_tags LIKE '%"hometown"%'
          AND sd.band_level BETWEEN 5.0 AND 7.0
    """
    cur.execute(query)
    results = cur.fetchall()
    assert len(results) == 1
    assert results[0][3] == 6.0

    conn.close()
