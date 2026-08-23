"""API Dependencies and Shared In-Memory Caches."""
import logging

logger = logging.getLogger("duolingo_speak.api")

# Global In-Memory Caches for Instant 0ms Word Lookup & Translations
TRANSLATION_CACHE: dict[str, str] = {}
IPA_CACHE: dict[str, str] = {}
SENTENCE_TRANSLATION_CACHE: dict[str, str] = {}
