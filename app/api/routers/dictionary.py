"""Dictionary & Translation API Router."""
import logging
import unicodedata
from urllib.parse import quote

import requests
from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import (
    IPA_CACHE,
    SENTENCE_TRANSLATION_CACHE,
    TRANSLATION_CACHE,
)
from app.api.schemas.chat import SentenceTranslateRequest
from app.core import ai_engine
from app.dictionary import DictionaryService
from app.storage import (
    get_all_saved_words,
    get_translated_word,
    save_translated_word,
)

logger = logging.getLogger("duolingo_speak.api.dictionary")
router = APIRouter(tags=["Dictionary & Localization"])


@router.get("/api/saved_words")
def api_get_saved_words(target_lang: str | None = Query(None, description="Optional target language filter")):
    words = get_all_saved_words(target_lang)
    return {"count": len(words), "words": words}


@router.post("/api/translate_sentence")
def api_translate_sentence(payload: SentenceTranslateRequest):
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    target_lang = payload.target_lang or "vi"
    cache_key = f"{target_lang}::{text}"

    if cache_key in SENTENCE_TRANSLATION_CACHE:
        return {"translation": SENTENCE_TRANSLATION_CACHE[cache_key], "cached": True}

    translation = ai_engine._professional_vietnamese_localization(
        text,
        character_name=payload.character_name or "",
        scenario_title=payload.scenario_title or "",
        context_history=payload.context_history or [],
    )
    if not translation:
        translation = ai_engine._fallback_llm_translate(text)

    if translation and translation.strip() != text.strip():
        SENTENCE_TRANSLATION_CACHE[cache_key] = translation
        return {"translation": translation, "cached": False}

    return {"translation": text, "cached": False}


@router.get("/api/translate_word")
def api_translate_word(
    word: str = Query(..., description="Word to look up"),
    target_lang: str = Query("vi", description="Target translation language code (vi, en-def, es, fr)"),
):
    clean_word = word.strip().strip(".,!?;:\"'()[]{}")
    if not clean_word:
        raise HTTPException(status_code=400, detail="Word cannot be empty")

    cache_key = f"{clean_word.lower()}_{target_lang}"
    lang_labels = {
        "vi": "Tiếng Việt",
        "en-def": "English Definition",
        "es": "Spanish",
        "fr": "French",
    }

    # 1. Check RAM Cache (0ms response)
    if cache_key in TRANSLATION_CACHE and not TRANSLATION_CACHE[cache_key].lower().startswith("definition of"):
        return {
            "word": clean_word,
            "target_lang": target_lang,
            "target_label": lang_labels.get(target_lang, "Translation"),
            "translation": TRANSLATION_CACHE[cache_key],
            "phonetic": IPA_CACHE.get(clean_word.lower(), f"/{clean_word.lower()}/"),
        }

    # 2. Check Offline Local Dictionary (data/dictionary.db)
    if target_lang == "vi":
        offline_match = DictionaryService.lookup(clean_word)
        if offline_match and offline_match.get("translation"):
            trans = offline_match["translation"]
            ipa = offline_match.get("phonetic") or f"/{clean_word.lower()}/"
            TRANSLATION_CACHE[cache_key] = trans
            IPA_CACHE[clean_word.lower()] = ipa
            return {
                "word": clean_word,
                "target_lang": target_lang,
                "target_label": lang_labels.get(target_lang, "Translation"),
                "translation": trans,
                "phonetic": ipa,
                "pos": offline_match.get("pos", ""),
            }

    # 3. Check Permanent SQLite Database
    db_word = get_translated_word(clean_word, target_lang)
    if db_word and db_word.get("translation") and not db_word["translation"].lower().startswith("definition of"):
        TRANSLATION_CACHE[cache_key] = db_word["translation"]
        IPA_CACHE[clean_word.lower()] = db_word["phonetic"]
        return db_word

    # 4. Fallback: High-Quality Online Dictionary Lookup
    tl_code = target_lang if target_lang != "en-def" else "en"
    real_translation = ""
    try:
        gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={tl_code}&dt=t&dt=bd&q={quote(clean_word)}"
        gt_res = requests.get(gt_url, timeout=4)
        if gt_res.status_code == 200:
            gt_data = gt_res.json()
            terms = []
            if len(gt_data) > 1 and gt_data[1]:
                for dict_entry in gt_data[1]:
                    if len(dict_entry) > 1 and dict_entry[1]:
                        terms.extend(dict_entry[1][:3])
            if not terms and gt_data[0] and gt_data[0][0]:
                terms.append(gt_data[0][0][0])
            if terms:
                unique_terms = list(dict.fromkeys(terms))[:3]
                raw_str = ", ".join(unique_terms)
                real_translation = unicodedata.normalize("NFC", raw_str).capitalize()
    except Exception as e:
        logger.warning(f"[Translate Word] Google Translate error: {e}")

    real_ipa = f"/{clean_word.lower()}/"
    try:
        dict_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{quote(clean_word.lower())}"
        dict_res = requests.get(dict_url, timeout=3)
        if dict_res.status_code == 200:
            dict_data = dict_res.json()
            if isinstance(dict_data, list) and dict_data[0].get("phonetics"):
                for p in dict_data[0]["phonetics"]:
                    if p.get("text"):
                        real_ipa = p["text"]
                        break
    except Exception as e:
        logger.warning(f"[Translate Word] Dictionary API error: {e}")

    if not real_translation:
        real_translation = clean_word.capitalize()

    if real_translation and not real_translation.lower().startswith("definition of"):
        save_translated_word(
            word=clean_word,
            target_lang=target_lang,
            target_label=lang_labels.get(target_lang, "Translation"),
            translation=real_translation,
            phonetic=real_ipa,
        )
        TRANSLATION_CACHE[cache_key] = real_translation
        IPA_CACHE[clean_word.lower()] = real_ipa

    return {
        "word": clean_word,
        "target_lang": target_lang,
        "target_label": lang_labels.get(target_lang, "Translation"),
        "translation": real_translation,
        "phonetic": real_ipa,
    }
