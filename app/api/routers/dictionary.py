"""Dictionary & Translation API Router."""
import html
import logging
import re
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


def _fetch_online_word_translation(clean_word: str, target_lang: str = "vi") -> str:
    """
    Fetch accurate online translation for words (including inflected forms like mentioned, ties, did).
    Tries multiple fallbacks:
    1. Google Translate Mobile endpoint (fast & reliable, avoids 429 bot blocks)
    2. Google Translate GTX Single Endpoint
    3. MyMemory Free Translation API
    4. LLM Translation Fallback via AI Engine
    """
    tl_code = target_lang if target_lang != "en-def" else "en"
    clean_lower = clean_word.strip().lower()

    # 1. Google Translate Mobile endpoint (iPhone User-Agent)
    try:
        gt_mobile_url = f"https://translate.google.com/m?q={quote(clean_word)}&sl=en&tl={tl_code}"
        headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15"}
        res = requests.get(gt_mobile_url, headers=headers, timeout=4)
        if res.status_code == 200:
            match = re.search(r'class="result-container">([^<]+)', res.text)
            if match:
                trans = html.unescape(match.group(1)).strip()
                if trans and trans.lower() != clean_lower and not trans.lower().startswith("definition of"):
                    return unicodedata.normalize("NFC", trans).capitalize()
    except Exception as e:
        logger.warning(f"[Translate Word] Google Translate Mobile error for '{clean_word}': {e}")

    # 2. Google Translate GTX Single Endpoint
    try:
        gt_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={tl_code}&dt=t&dt=bd&q={quote(clean_word)}"
        gt_res = requests.get(gt_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=3)
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
                trans = unicodedata.normalize("NFC", raw_str).capitalize()
                if trans and trans.lower() != clean_lower and not trans.lower().startswith("definition of"):
                    return trans
    except Exception as e:
        logger.warning(f"[Translate Word] Google Translate GTX error for '{clean_word}': {e}")

    # 3. MyMemory Free Translation API
    try:
        mm_url = f"https://api.mymemory.translated.net/get?q={quote(clean_word)}&langpair=en|{tl_code}"
        res = requests.get(mm_url, timeout=3)
        if res.status_code == 200:
            data = res.json()
            trans = data.get("responseData", {}).get("translatedText", "").strip()
            if trans and trans.lower() != clean_lower and not trans.lower().startswith("definition of"):
                return unicodedata.normalize("NFC", trans).capitalize()
    except Exception as e:
        logger.warning(f"[Translate Word] MyMemory API error for '{clean_word}': {e}")

    # 4. LLM Fallback via AI Engine
    try:
        llm_trans = ai_engine._fallback_llm_translate(clean_word)
        if llm_trans and llm_trans.strip().lower() != clean_lower and not llm_trans.lower().startswith("definition of"):
            return llm_trans.strip().capitalize()
    except Exception as e:
        logger.warning(f"[Translate Word] LLM translation fallback error for '{clean_word}': {e}")

    return ""


@router.get("/api/saved_words")
def api_get_saved_words(target_lang: str | None = Query(None, description="Optional target language filter")):
    words = get_all_saved_words(target_lang)
    lang_code = target_lang or "vi"
    lang_labels = {"vi": "Tiếng Việt", "en-def": "English Definition", "es": "Spanish", "fr": "French"}

    # Auto-heal any legacy saved words stored with untranslated original text (e.g. mentioned, ties, did)
    for w in words:
        word_str = str(w.get("word", "")).strip()
        trans_str = str(w.get("translation", "")).strip()
        if word_str and (not trans_str or trans_str.lower() == word_str.lower() or trans_str.lower().startswith("definition of")):
            new_trans = _fetch_online_word_translation(word_str, w.get("target_lang") or lang_code)
            if new_trans:
                w["translation"] = new_trans
                save_translated_word(
                    word=word_str,
                    target_lang=w.get("target_lang") or lang_code,
                    target_label=w.get("target_label") or lang_labels.get(lang_code, "Translation"),
                    translation=new_trans,
                    phonetic=w.get("phonetic", f"/{word_str.lower()}/"),
                )

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
    if cache_key in TRANSLATION_CACHE:
        cached_val = TRANSLATION_CACHE[cache_key]
        if not cached_val.lower().startswith("definition of") and cached_val.lower() != clean_word.lower():
            return {
                "word": clean_word,
                "target_lang": target_lang,
                "target_label": lang_labels.get(target_lang, "Translation"),
                "translation": cached_val,
                "phonetic": IPA_CACHE.get(clean_word.lower(), f"/{clean_word.lower()}/"),
            }

    # 2. Check Offline Local Dictionary (data/dictionary.db)
    if target_lang == "vi":
        offline_match = DictionaryService.lookup(clean_word)
        if offline_match and offline_match.get("translation"):
            trans = offline_match["translation"].strip()
            if trans.lower() != clean_word.lower() and not trans.lower().startswith("definition of"):
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
    if db_word and db_word.get("translation"):
        trans = db_word["translation"].strip()
        if trans.lower() != clean_word.lower() and not trans.lower().startswith("definition of"):
            TRANSLATION_CACHE[cache_key] = trans
            IPA_CACHE[clean_word.lower()] = db_word["phonetic"]
            return db_word

    # 4. Fallback: Multi-level Online Translation Lookup (Google Translate / MyMemory / LLM)
    real_translation = _fetch_online_word_translation(clean_word, target_lang)

    # 5. Fetch Phonetic / IPA from dictionary API
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

    # Fallback to LLM if still empty or equal to original word
    if not real_translation or real_translation.lower() == clean_word.lower():
        real_translation = ai_engine._fallback_llm_translate(clean_word)

    # Ensure final fallback never returns raw English
    if not real_translation or real_translation.lower() == clean_word.lower():
        real_translation = f"Từ: {clean_word}"

    if real_translation and real_translation.lower() != clean_word.lower() and not real_translation.lower().startswith("definition of"):
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
