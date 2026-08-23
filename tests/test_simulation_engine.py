"""
Unit tests for Real-World Roleplay Simulation Engine (TASK-019).
Tests app/scenarios/simulation_engine.py, app/scenarios/__init__.py backwards compatibility,
dynamic branching, evaluation hook triggers, and prompt constructor integration.
"""

import sqlite3

import pytest

from app.rag.prompt_constructor import PromptContext, construct_system_prompt
from app.scenarios import (
    DEFAULT_SCENARIOS,
    RealWorldSimulationEngine,
    build_simulation_directives,
    evaluate_hooks,
    get_active_scenario,
    get_scenario,
    list_scenarios,
    select_branch,
)


@pytest.fixture
def memory_db():
    """Create an in-memory SQLite database populated with standard 12 schema tables."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_units (
            id TEXT PRIMARY KEY,
            template_type TEXT NOT NULL,
            title TEXT NOT NULL,
            topic_tags TEXT DEFAULT '[]',
            target_band_min REAL,
            target_band_max REAL,
            register TEXT,
            source_citation TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            version INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY,
            content_unit_id TEXT UNIQUE REFERENCES content_units(id),
            setting TEXT,
            ai_role TEXT,
            user_role TEXT,
            grammar_required TEXT DEFAULT '[]',
            vocabulary_core TEXT DEFAULT '[]',
            vocabulary_stretch TEXT DEFAULT '[]'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenario_branches (
            id TEXT PRIMARY KEY,
            scenario_id TEXT REFERENCES scenarios(id),
            branch_type TEXT CHECK(branch_type IN ('low_band','high_band')),
            condition_rule TEXT,
            ai_response_style TEXT,
            example_text TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluation_hooks (
            id TEXT PRIMARY KEY,
            scenario_id TEXT REFERENCES scenarios(id),
            trigger_condition TEXT,
            ai_reaction TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sample_dialogues (
            id TEXT PRIMARY KEY,
            content_unit_id TEXT NOT NULL REFERENCES content_units(id),
            band_level REAL NOT NULL,
            turn_type TEXT,
            function_tag TEXT,
            ai_line TEXT NOT NULL,
            user_model_answer TEXT NOT NULL,
            embedding BLOB,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_content_exposure (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            sample_dialogue_id TEXT,
            exposed_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Seed sample scenario data
    cursor.execute("""
        INSERT INTO content_units (id, template_type, title, topic_tags, target_band_min, target_band_max, register)
        VALUES ('cu_job_interview', 'scenario', 'Job Interview Simulation', '["career","work"]', 5.0, 8.5, 'formal')
    """)

    cursor.execute("""
        INSERT INTO scenarios (id, content_unit_id, setting, ai_role, user_role, grammar_required, vocabulary_core, vocabulary_stretch)
        VALUES ('sc_job_interview', 'cu_job_interview', 'Tech Company Conference Room', 'Hiring Manager', 'Job Candidate',
                '["past_perfect", "conditional_2"]', '["experience", "strengths", "qualifications"]', '["synergy", "spearhead"]')
    """)

    cursor.execute("""
        INSERT INTO scenario_branches (id, scenario_id, branch_type, condition_rule, ai_response_style, example_text)
        VALUES
        ('b1', 'sc_job_interview', 'low_band', 'user_band < 6.0', 'Ask basic questions about work history slowly and clearly.', 'Tell me about your last job.'),
        ('b2', 'sc_job_interview', 'high_band', 'user_band >= 6.0', 'Ask probing behavioral questions requiring STAR method responses.', 'Describe a crisis you resolved under pressure.')
    """)

    cursor.execute("""
        INSERT INTO evaluation_hooks (id, scenario_id, trigger_condition, ai_reaction)
        VALUES
        ('h1', 'sc_job_interview', 'salary expectation', 'Pivot back to role responsibilities before discussing specific numbers.'),
        ('h2', 'sc_job_interview', 'weakness', 'Praise self-awareness and ask how candidate actively works on it.')
    """)

    conn.commit()
    yield conn
    conn.close()


def test_backwards_compatibility_imports():
    """Verify legacy imports from app.scenarios continue working seamlessly."""
    engine = RealWorldSimulationEngine()
    assert engine is not None

    scenarios_list = list_scenarios()
    assert isinstance(scenarios_list, list)
    assert len(scenarios_list) > 0

    sc = get_scenario("det_childhood_memory")
    assert sc is not None
    assert sc["title"] == "Childhood Memories"
    assert "det_childhood_memory" in DEFAULT_SCENARIOS


def test_get_active_scenario_fallback():
    """Test get_active_scenario falls back to static scenario when not in DB."""
    sc = get_active_scenario("everyday_chat")
    assert sc is not None
    assert sc["id"] == "everyday_chat"
    assert "Everyday" in sc["title"]
    assert sc["ai_role"] == "Interactive Roleplay Partner"
    assert sc["user_role"] == "English Learner"
    assert sc["is_db"] is False


def test_get_active_scenario_from_db(memory_db):
    """Test get_active_scenario correctly fetches full metadata from DB tables."""
    sc = get_active_scenario("sc_job_interview", conn=memory_db)
    assert sc is not None
    assert sc["id"] == "sc_job_interview"
    assert sc["title"] == "Job Interview Simulation"
    assert sc["ai_role"] == "Hiring Manager"
    assert sc["user_role"] == "Job Candidate"
    assert sc["register"] == "formal"
    assert "experience" in sc["vocabulary_core"]
    assert "past_perfect" in sc["grammar_required"]
    assert len(sc["branches"]) == 2
    assert len(sc["evaluation_hooks"]) == 2
    assert sc["is_db"] is True


def test_select_branch_low_and_high_band(memory_db):
    """Test select_branch dynamically chooses low_band vs high_band branches."""
    # Low band test (< 6.0)
    low_branch = select_branch("sc_job_interview", user_band=5.0, conn=memory_db)
    assert low_branch["branch_type"] == "low_band"
    assert "basic questions" in low_branch["ai_response_style"]

    # High band test (>= 6.0)
    high_branch = select_branch("sc_job_interview", user_band=7.0, conn=memory_db)
    assert high_branch["branch_type"] == "high_band"
    assert "behavioral questions" in high_branch["ai_response_style"]

    # Fallback branch test when scenario has no DB branches
    fallback_low = select_branch("everyday_chat", user_band=4.5)
    assert fallback_low["branch_type"] == "low_band"
    assert "Supportive" in fallback_low["ai_response_style"]

    fallback_high = select_branch("everyday_chat", user_band=6.5)
    assert fallback_high["branch_type"] == "high_band"
    assert "Challenging" in fallback_high["ai_response_style"]


def test_evaluate_hooks(memory_db):
    """Test evaluation hooks matching against user utterances."""
    sc = get_active_scenario("sc_job_interview", conn=memory_db)

    # Empty utterance
    assert evaluate_hooks(sc, "", conn=memory_db) == []

    # Custom hook trigger test ("salary expectation")
    triggered = evaluate_hooks(sc, "My salary expectation is 80k annually.", conn=memory_db)
    assert len(triggered) >= 1
    assert any(t["id"] == "h1" for t in triggered)
    assert any("Pivot back" in t["ai_reaction"] for t in triggered)

    # Target vocabulary usage trigger test ("experience")
    vocab_triggered = evaluate_hooks(sc, "I have extensive experience leading teams.", conn=memory_db)
    assert len(vocab_triggered) >= 1
    assert any("experience" in t["trigger_condition"] for t in vocab_triggered)

    # Target grammar usage trigger test ("past_perfect")
    grammar_triggered = evaluate_hooks(sc, "I had completed past_perfect project before the deadline.", conn=memory_db)
    assert len(grammar_triggered) >= 1
    assert any("past_perfect" in t["trigger_condition"] for t in grammar_triggered)


def test_build_simulation_directives(memory_db):
    """Test build_simulation_directives constructs full directive package."""
    directives = build_simulation_directives(
        scenario_id="sc_job_interview",
        user_id="user_test",
        user_band=7.5,
        user_utterance="What is your salary expectation for this position?",
        conn=memory_db,
    )

    assert directives["scenario_id"] == "sc_job_interview"
    assert directives["title"] == "Job Interview Simulation"
    assert directives["ai_role"] == "Hiring Manager"
    assert directives["branch"]["branch_type"] == "high_band"
    assert len(directives["triggered_hooks"]) > 0

    prompt_str = directives["directives_prompt"]
    assert "=== REAL-WORLD ROLEPLAY SIMULATION: Job Interview Simulation ===" in prompt_str
    assert "AI Role: Hiring Manager" in prompt_str
    assert "Active Branch Mode (HIGH_BAND)" in prompt_str
    assert "Triggered Evaluation Hooks:" in prompt_str


def test_prompt_constructor_integration(memory_db):
    """Test integration of simulation directives with construct_system_prompt."""
    directives = build_simulation_directives(
        scenario_id="sc_job_interview",
        user_id="user_test",
        user_band=6.5,
        conn=memory_db,
    )

    context = PromptContext(
        user_id="user_test",
        band_estimate=6.5,
        topic_tag="career",
        simulation_directives=directives["directives_prompt"],
    )

    system_prompt = construct_system_prompt(context)
    assert "### ROLEPLAY SIMULATION DIRECTIVES" in system_prompt
    assert "Job Interview Simulation" in system_prompt
    assert "Hiring Manager" in system_prompt
    assert "Active Branch Mode (HIGH_BAND)" in system_prompt
