# PLAN: TASK-010 — Optimistic Client-Side STT & Asynchronous Acoustic Extraction

> **Task ID:** TASK-010  
> **Phase:** Phase 4 (Ultra-Low-Latency & Real-Time Voice Streaming Optimization)  
> **Priority:** P0-Critical  
> **Target Files:** `static/js/speech.js`, `app/api/routers/audio.py`, `tests/test_optimistic_stt.py`

---

## 🎯 Goal & Acceptance Criteria
- [x] Implement `POST /api/audio/extract_acoustic_metrics` in `app/api/routers/audio.py` for background acoustic feature extraction (WPM, pauses, pitch/rhythm, fluency tier).
- [x] Update `static/js/speech.js` for Optimistic Client-Side STT: immediately emit browser-recognized transcript to `onResult(text, true, null)` without waiting for server ASR, and extract acoustic metrics in an unblocked background fetch.
- [x] Create unit & integration tests in `tests/test_optimistic_stt.py` verifying background acoustic extraction endpoint and optimistic STT contract.
- [x] Pass `pytest tests/test_optimistic_stt.py` and `python3 pipeline/scripts/verify.py` 100%.

---

## 📍 Execution Plan (Atomic Steps)

### Step 1: Update Backend Endpoint `app/api/routers/audio.py` [x]
- Add `POST /api/audio/extract_acoustic_metrics` endpoint to accept audio file blob + transcript string.
- Invoke `ai_engine._compute_speech_acoustic_metrics(transcript, audio_bytes)` to compute WPM, pauses, pronunciation score, duration, and fluency tier.
- Return structured acoustic feedback response `{"status": "success", "speech_metrics": metrics, "transcript": transcript}`.

### Step 2: Update Frontend Client `static/js/speech.js` [x]
- Update `SpeechHandler` to send client-side Web Speech API transcript instantly to `onResult(text, true, null)` when recording ends.
- Asynchronously dispatch audio recording blob to `/api/audio/extract_acoustic_metrics` without blocking conversation turn execution.
- Store/emit acoustic metrics upon arrival for UI metrics display.

### Step 3: Implement `tests/test_optimistic_stt.py` [x]
- Test `/api/audio/extract_acoustic_metrics` endpoint with audio upload and transcript text.
- Test endpoint return structure (`speech_metrics` with `wpm`, `pauses`, `pronunciation_score`, `fluency_tier`, `acoustic_feedback`).
- Test `/api/transcribe_audio` instant fallback and client-side STT integration contracts.

### Step 4: Run Deterministic Verification & Finalize [x]
- Run `pytest tests/test_optimistic_stt.py`.
- Run `python3 pipeline/scripts/verify.py`.
- Update `STATUS.md`, `PROGRESS_LOG.md`, `PLAN.md`, and mark `[x] DONE` in `Tasks_list.md`.
