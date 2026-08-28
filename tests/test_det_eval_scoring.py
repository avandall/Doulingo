import asyncio

import pytest

from app.core.ai_engine import AIEngine, ai_engine
from app.scenarios import get_scenario


def test_evaluate_det_speech_dynamic_components():
    async def _run():
        engine = ai_engine
        scenario = get_scenario("det_childhood_memory") or {
            "id": "det_childhood_memory",
            "title": "A Memorable Childhood Experience",
            "description": "Describe a vivid childhood memory."
        }

        user_speech_short = "I remember when I was young. I played with my dog in the park."
        res_short = await engine.evaluate_det_speech(
            scenario=scenario,
            user_speech=user_speech_short,
            duration_seconds=30,
            mode="read_then_speak",
            wpm=90,
            pause_count=3,
            filler_count=2
        )

        assert "det_score" in res_short
        assert "fluency_score" in res_short
        assert "grammar_score" in res_short
        assert "vocabulary_score" in res_short
        assert "coherence_score" in res_short
        assert "sentence_upgrades" in res_short
        assert "sample_native_response" in res_short

        scores = [res_short["fluency_score"], res_short["grammar_score"], res_short["vocabulary_score"], res_short["coherence_score"]]
        assert not all(s == 95 for s in scores), f"Scores should not all be fixed at 95: {scores}"

        upgrades = res_short["sentence_upgrades"]
        assert len(upgrades) > 0
        assert "original" in upgrades[0]
        assert "upgraded" in upgrades[0]
        assert "explanation" in upgrades[0]

    asyncio.run(_run())


def test_evaluate_det_speech_longer_response():
    async def _run():
        engine = ai_engine
        scenario = get_scenario("det_ai_future") or {
            "id": "det_ai_future",
            "title": "Artificial Intelligence & Future of Work",
            "description": "Discuss how AI will transform jobs and society."
        }

        user_speech_long = (
            "In my opinion, artificial intelligence will drastically transform the modern workplace. "
            "Repetitive routine tasks will certainly be automated, freeing up human professionals to focus on creative strategy. "
            "However, governments and educational institutions must collaborate to retrain the workforce so that workers are not left behind. "
            "Critical thinking and emotional intelligence will become increasingly valuable in the coming decades."
        )

        res_long = await engine.evaluate_det_speech(
            scenario=scenario,
            user_speech=user_speech_long,
            duration_seconds=50,
            mode="read_then_speak",
            wpm=135,
            pause_count=1,
            filler_count=0
        )

        assert res_long["det_score"] >= 70
        assert "examiner_critique" in res_long
        assert len(res_long["examiner_critique"]) > 20
        assert res_long["acoustic_metrics"]["wpm"] == 135
        assert res_long["acoustic_metrics"]["filler_count"] == 0

    asyncio.run(_run())


def test_parse_raw_json_preserves_det_schema():
    engine = ai_engine
    raw_payload = '''```json
    {
        "det_score": 125,
        "cefr_level": "B2 Upper-Intermediate",
        "fluency_score": 82,
        "grammar_score": 79,
        "vocabulary_score": 84,
        "coherence_score": 80,
        "examiner_critique": "Thí sinh diễn đạt tương đối trôi chảy.",
        "sentence_upgrades": [
            {
                "original": "AI is good for work",
                "upgraded": "AI significantly enhances workplace productivity",
                "explanation": "Nâng cấp từ vựng học thuật enhancements."
            }
        ],
        "sample_native_response": "Regarding artificial intelligence, its impact is undeniable."
    }
    ```'''
    parsed = engine._parse_raw_json(raw_payload)
    assert parsed.get("det_score") == 125
    assert parsed.get("fluency_score") == 82
    assert len(parsed.get("sentence_upgrades", [])) == 1
