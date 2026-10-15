import uuid
import pytest
from app.storage.db import (
    init_db,
    create_user,
    authenticate_user,
    get_user_by_id,
    update_user_mother_tongue,
    update_user_api_keys,
    save_user_vocabulary_word,
    get_user_vocabulary,
    delete_user_vocabulary_word,
)
from app.api.routers.auth import create_token, verify_token, get_current_user_from_header
from app.core.ai_engine import AIEngine


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_user_creation_and_auth():
    username = f"test_learner_{uuid.uuid4().hex[:8]}"
    password = "SecretPassword123"
    mother_tongue = "vi"

    # Create user
    user = create_user(username, password, mother_tongue=mother_tongue)
    assert user is not None
    assert user["username"] == username
    assert user["mother_tongue"] == "vi"

    # Authenticate valid
    auth_user = authenticate_user(username, password)
    assert auth_user is not None
    assert auth_user["id"] == user["id"]

    # Authenticate invalid
    bad_auth = authenticate_user(username, "WrongPassword")
    assert bad_auth is None


def test_token_generation_and_decoding():
    uname = f"token_user_{uuid.uuid4().hex[:8]}"
    user = create_user(uname, "Pass1234", mother_tongue="ja")
    assert user is not None

    token = create_token(user["id"], user["username"])
    assert isinstance(token, str)

    payload = verify_token(token)
    assert payload is not None
    assert payload["sub"] == user["id"]
    assert payload["username"] == uname

    # Verify header resolution
    resolved = get_current_user_from_header(f"Bearer {token}")
    assert resolved is not None
    assert resolved["id"] == user["id"]
    assert resolved["mother_tongue"] == "ja"


def test_mother_tongue_and_byok_keys():
    uname = f"byok_user_{uuid.uuid4().hex[:8]}"
    user = create_user(uname, "Pass1234", mother_tongue="vi")
    assert user is not None

    # Update mother tongue
    ok = update_user_mother_tongue(user["id"], "es")
    assert ok is True
    updated = get_user_by_id(user["id"])
    assert updated is not None
    assert updated["mother_tongue"] == "es"

    # Update BYOK keys
    keys_ok = update_user_api_keys(
        user["id"],
        {
            "groq_api_key": "gsk_custom_groq_123",
            "gemini_api_key": "AIzaSyCustomGemini",
            "openai_api_key": "sk-custom-openai",
        },
    )
    assert keys_ok is True

    user_with_keys = get_user_by_id(user["id"])
    assert user_with_keys is not None
    assert user_with_keys["custom_api_keys"]["groq_api_key"] == "gsk_custom_groq_123"
    assert user_with_keys["custom_api_keys"]["gemini_api_key"] == "AIzaSyCustomGemini"
    assert user_with_keys["custom_api_keys"]["openai_api_key"] == "sk-custom-openai"


def test_isolated_vocabulary_notebook():
    user_a = create_user(f"user_a_{uuid.uuid4().hex[:8]}", "Pass1234", mother_tongue="vi")
    user_b = create_user(f"user_b_{uuid.uuid4().hex[:8]}", "Pass1234", mother_tongue="ko")
    assert user_a is not None and user_b is not None

    # User A saves a word
    item_a = save_user_vocabulary_word(
        user_id=user_a["id"],
        word="eloquent",
        translation="hùng hồn, lưu loát",
        phonetic="/ˈel.ə.kwənt/",
        target_lang="vi",
    )
    assert item_a["word"] == "eloquent"

    # User B should NOT see user A's word
    words_b = get_user_vocabulary(user_b["id"])
    assert len(words_b) == 0

    # User A should see their word
    words_a = get_user_vocabulary(user_a["id"])
    assert len(words_a) == 1
    assert words_a[0]["word"] == "eloquent"

    # Delete word
    deleted = delete_user_vocabulary_word(user_a["id"], item_a["id"])
    assert deleted is True
    assert len(get_user_vocabulary(user_a["id"])) == 0


@pytest.mark.anyio
async def test_bilingual_examiner_critique_structure():
    ai = AIEngine()
    result = await ai.evaluate_det_speech(
        scenario={"id": "ai_future", "title": "AI & Education", "description": "Discuss future of tech"},
        user_speech="I strongly believe that artificial intelligence will transform education significantly by personalizing learning paths.",
        duration_seconds=35,
        wpm=110,
        pause_count=1,
        filler_count=0,
        mother_tongue="vi",
    )

    assert "det_score" in result
    assert "ielts_band" in result
    assert "examiner_critique" in result
    assert "examiner_critique_sections" in result

    # When mother_tongue is 'vi', is_bilingual should be True
    assert result.get("is_bilingual") is True
    assert result.get("target_lang") == "vi"

    sections = result["examiner_critique_sections"]
    assert "interaction" in sections
    assert "grammar_vocab" in sections
    assert "fluency" in sections
    assert "advice" in sections
