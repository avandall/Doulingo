# Implementation Plan — TASK-008: TTS Audio Output Streamer (`app/tts_streamer.py`)

## Goal
Implement `app/tts_streamer.py` to stream TTS audio output for `ai_utterance`. The module encapsulates multi-provider speech synthesis (ElevenLabs, Edge-TTS, gTTS) into clean streaming and batch audio APIs, providing explicit `text_only_mode` fallback when audio is disabled or unavailable.

## Acceptance Criteria
- [x] Implement `TTSStreamResult` dataclass with fields `audio_bytes: bytes | None`, `content_type: str`, `text_only_mode: bool`, `error_message: str | None`.
- [x] Implement `TTSStreamer` class & module functions:
  - `generate_audio(text: str, char_id: str = "lily", text_only_mode: bool = False) -> TTSStreamResult`
  - `stream_audio_chunks(text: str, char_id: str = "lily", text_only_mode: bool = False) -> AsyncIterator[bytes]`
- [x] Support explicit `text_only_mode` fallback flag without throwing exceptions.
- [x] Implement robust error handling so TTS service degradation logs warning and returns text-only response cleanly.
- [x] Implement unit test suite in `tests/test_tts_streamer.py`.
- [x] `python3 H_docs/scripts/verify.py` passes 100% (Ruff, Mypy, Bandit, Pytest).

## Proposed Steps

### Step 1: Implement `app/tts_streamer.py` [x]
- Define `TTSStreamResult` dataclass.
- Implement `TTSStreamer` class with `generate_audio` and `stream_audio_chunks` methods.
- Integrate with `app.tts_service` for underlying ElevenLabs/Edge-TTS/gTTS synthesis.
- Handle `text_only_mode` and error fallback gracefully.

### Step 2: Implement Unit Tests & Run Verification (Phase 4) [x]
- Create `tests/test_tts_streamer.py` to test:
  - Batch audio generation via `generate_audio`.
  - Async chunk streaming via `stream_audio_chunks`.
  - `text_only_mode=True` behavior.
  - Resilience under invalid inputs or service exceptions.
- Run `python3 H_docs/scripts/verify.py` and verify zero errors.

## Status
- **Current Phase:** Phase 6 (COMMIT) & Phase 7 (REPORT) DONE
- **Iteration:** 36
- **Result:** PASS

