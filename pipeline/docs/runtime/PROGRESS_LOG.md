# PROGRESS LOG
# Nhật ký tiến độ chi tiết — Ghi lại toàn bộ lịch sử thao tác & phát sinh

> **Trạng thái:** RUNTIME (Auto-generated) | **Cập nhật:** 2026-08-27 14:53

---

## 📅 Lịch sử thực thi

### [2026-08-27 23:57] — Hoàn thành TASK-013
- **Task ID:** TASK-013 (Sentence-Level Streaming & Direct Chunked Audio Synthesis)
- **Hành động:**
  - Triển khai `split_sentences(text)` và `stream_sentence_level_tts(text, char_id, tld)` trong `app/audio/tts_service.py` hỗ trợ phân tách câu tự nhiên theo dấu chấm/hỏi/cảm/xuống dòng và stream audio chunk MP3 cho câu đầu tiên ngay lập tức (<1.0s TTFA).
  - Cập nhật `TTSStreamer` trong `app/audio/tts_streamer.py` bổ sung phương thức `stream_sentence_audio_chunks` và hàm tiện ích `stream_sentence_audio_response`.
  - Export các hàm streaming mới trong `app/audio/__init__.py`.
  - Cập nhật router API `app/api/routers/audio.py` bổ sung endpoint `GET /api/tts/stream` và cờ `stream=true` cho `GET /api/tts` trả về StreamingResponse audio/mpeg chunked cho trình duyệt.
  - Tái cấu trúc hàm `playTTS(text, charId)` trong `static/js/app.js` cho phép HTML5 Audio element phát trực tiếp stream URL từ chunk đầu tiên mà không phải chờ nạp toàn bộ blob file MP3.
  - Viết bộ test suite `tests/test_sentence_stream.py` (7 test cases) kiểm tra sentence splitting, sentence audio streaming generator, streaming API endpoints. Pass 100% (7/7).
  - Kiểm tra chất lượng tổng thể (Ruff, Mypy, Bandit, Pytest) qua `python3 pipeline/scripts/verify.py` đạt **PASS 100%**.
  - Đánh dấu `[x] DONE` cho `TASK-013` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-27 23:33] — Hoàn thành TASK-011
- **Task ID:** TASK-011 (Decoupled Fast Voice LLM & Background Evaluation Pipeline)
- **Hành động:**
  - Triển khai `process_turn_fast()` trong `app/core/ai_engine.py` giúp AI sinh câu thoại plain text ngắn gọn (~30-40 tokens) với độ trễ siêu thấp (<400ms), bóc tách khỏi luồng chấm điểm nặng.
  - Triển khai `evaluate_turn_background()` và bộ nhớ `BACKGROUND_EVAL_STORE` trong `app/core/ai_engine.py` để tính toán toàn bộ điểm số ngữ pháp, độ trôi chảy, bản dịch tiếng Việt, gợi ý bản xứ và ghi nhật ký Error Journal trong luồng bất đồng bộ ngầm.
  - Cập nhật `app/api/schemas/chat.py` bổ sung Pydantic model `FastTurnRequest`.
  - Cập nhật `app/api/routers/chat.py` bổ sung endpoint `POST /api/process_turn_fast` (tự động kích hoạt `BackgroundTasks.add_task` để chấm điểm ngầm) và endpoint `GET /api/turn_evaluation/{turn_id}` cho phép UI truy vấn kết quả đánh giá chi tiết sau khi AI cất lời.
  - Viết bộ unit & integration test suite `tests/test_decoupled_voice_llm.py` (4 test cases) kiểm tra `process_turn_fast`, `evaluate_turn_background`, fast turn API endpoint và turn evaluation polling API endpoint. Pass 100% (4/4).
  - Kiểm tra chất lượng tổng thể (Ruff, Mypy, Bandit, Pytest) qua `python3 pipeline/scripts/verify.py` đạt **PASS 100%**.
  - Đánh dấu `[x] DONE` cho `TASK-011` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-26 21:21] — Khởi tạo TASK-001
- **Task ID:** TASK-001 (Crawl & Seed Initial Datasets)
- **Hành động:** 
  - Khởi tạo PLAN.md và STATUS.md cho TASK-001.
  - Phân tích bối cảnh và yêu cầu cho `scripts/seed_data.py`, `app/data/vocab_bank.json` (>1000 từ vựng A1-B1) và `app/data/sample_dialogue_bank.json` (>100 câu thoại mẫu).

### [2026-08-26 21:22] — Hoàn thành TASK-001
- **Hành động:**
  - Viết `scripts/seed_data.py` tự động tích hợp nguồn từ vựng Oxford/Cambridge CEFR A1-B1 kết hợp dữ liệu từ `data/dictionary.db`.
  - Sinh thành công `app/data/vocab_bank.json` với **2,445 từ vựng** (yêu cầu > 1000).
  - Sinh thành công `app/data/sample_dialogue_bank.json` với **150 câu thoại mẫu** phân loại theo level, persona, topic, dialogue_act (yêu cầu > 100).
  - Kiểm định static analysis (Ruff & Mypy) pass 100%.
  - Cập nhật trạng thái `TASK-001` thành `[x] DONE` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-26 21:26] — Khởi tạo TASK-002
- **Task ID:** TASK-002 (Build Vocabulary Bank & Heuristic Level Checker)
- **Hành động:**
  - Tạo `PLAN.md` 4 bước và cập nhật `STATUS.md` cho TASK-002.

### [2026-08-26 21:27] — Hoàn thành TASK-002
- **Hành động:**
  - Viết module `app/core/heuristic_checker.py` thực hiện:
    1. Đọc dữ liệu `app/data/vocab_bank.json` và ánh xạ rank level CEFR (Pre-A1 -> C2) và 20-level integer scale.
    2. Đếm từ, đếm câu, và tính độ dài câu trung bình.
    3. Tra từ vựng vượt trần `check_level_ceiling(text, target_level)` với thời gian thực thi siêu nhanh **< 0.5ms** (đạt yêu cầu < 5ms).
  - Viết bộ test `tests/test_heuristic_checker.py` gồm 8 test cases kiểm tra initialization, sentence analysis, level ceiling pass/violate, integer level mapping, benchmarking, tuple unpacking & dict indexing.
  - Sửa lỗi linting import/SIM102 và chạy `python3 pipeline/scripts/verify.py --test-target tests/test_heuristic_checker.py` đạt **PASS 100%** (Ruff, Mypy, Bandit, Pytest đều PASS).
  - Đánh dấu `[x] DONE` cho `TASK-002` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-26 21:31] — Hoàn thành TASK-003
- **Task ID:** TASK-003 (Build Dialogue Exemplar Bank & Hybrid RAG Engine)
- **Hành động:**
  - Viết module `app/core/exemplar_rag.py` thực hiện:
    1. Metadata Filtering (level, persona, topic, dialogue_act) với cơ chế progressive relaxation fallback 8 tầng đảm bảo luôn trả về 2-3 câu mẫu chuẩn.
    2. TF-IDF + Cosine Distance Semantic Search đối soát câu mẫu với `state_summary`.
    3. Maximal Marginal Relevance (MMR) ranking để đảm bảo tính đa dạng của các câu thoại trả về.
    4. Subclass `DialogueExemplar(dict)` hỗ trợ song song truy cập dict `ex['text']` và property `ex.text`.
    5. Helper `format_exemplars_for_prompt(exemplars)` định dạng câu thoại cho Gemini prompt injection.
  - Viết bộ test suite `tests/test_exemplar_rag.py` (11 test cases) đạt 100% pass với độ trễ retrieval < 1ms (< 15ms benchmark).
  - Kiểm tra static analysis (Ruff & Mypy) pass 100% không cảnh báo.
  - Chạy `python3 pipeline/scripts/verify.py --test-target tests/test_exemplar_rag.py` đạt **PASS 100%**.
  - Cập nhật `pipeline/docs/context/Tasks_list.md` đánh dấu `[x] DONE` cho TASK-003.

### [2026-08-26 21:44] — Hoàn thành TASK-004
- **Task ID:** TASK-004 (Implement Structured Output CoT & Heuristic Validation Loop Engine)
- **Hành động:**
  - Tạo `app/core/prompt_factory.py` hỗ trợ re-export `PromptFactory`, `get_prompt_factory` và cung cấp hướng dẫn `COT_SCHEMA_INSTRUCTIONS`.
  - Cập nhật `app/core/ai_engine.py`:
    1. Ngay Call 1 yêu cầu LLM sinh JSON Structured Output CoT (`natural_draft`, `vocab_check`, `final_response`).
    2. Tích hợp `HeuristicChecker.check_level_ceiling`: nếu PASS thì xuất kết quả ngay trong 1 API call.
    3. Nếu Heuristic Check FAIL, hệ thống tự động feed back lỗi từ các từ vi phạm ceiling cho LLM hạ cấp trong retry loop đến khi PASS (hoặc tối đa `max_retries`).
    4. Hàm `_parse_json_response` trích xuất `natural_draft`, `vocab_check`, và `final_response` / `ai_response` đồng thời.
  - Mở rộng `tests/test_ai_engine.py` thêm 4 unit tests mới kiểm định Structured CoT parsing, single-call PASS path, retry feedback loop trên vi phạm từ vựng, và `process_turn` CoT integration (100% pass 10/10 tests).
  - Kiểm tra static analysis (Ruff, Mypy, Bandit, Pytest) thông qua `uv run python3 pipeline/scripts/verify.py --test-target tests/test_ai_engine.py` đạt **PASS 100%**.
  - Cập nhật `pipeline/docs/context/Tasks_list.md` đánh dấu `[x] DONE` cho `TASK-004`.

### [2026-08-26 21:57] — Fix Iteration 2 (Executor Fix Role)
- **Task ID:** TASK-004
- **Hành động:**
  - Tiếp nhận kết quả từ chối review 1/2 do Tier 1 Pytest verification check thất bại.
  - Đọc `pipeline/docs/runtime/DEBATE_LOG.md` và xác định 4 nguyên nhân gốc rễ trong `app/core/ai_engine.py`:
    1. Network timeout (`ReadTimeout`) trong `evaluate_det_speech` khi gọi Gemini/Groq/OpenAI mà không có khối `try...except` bọc ngoài.
    2. Thiếu `{title}` trong các mẫu câu opener thuộc sentiment `confused`, `negative`, `neutral` dẫn đến trượt test `test_context_aware_fallback_topic_continuity` và topic-shift tests.
    3. Trùng lặp chuỗi trong vòng lặp 10 lượt `test_10_turns_consecutive_anti_repetition` do giới hạn cửa sổ lịch sử và chọn fallback cố định.
    4. Nhân đôi chuỗi `feedback_instruction` liên tục trong `_call_llm_with_heuristic_loop` khi retry.
  - Sửa triệt để các vấn đề trên trong `app/core/ai_engine.py`.
  - Chạy lại `python3 pipeline/scripts/verify.py` đạt **PASS 100%** (Ruff, Mypy, Bandit, và toàn bộ 257/257 Pytest tests đều GREEN ✅).
  - Cập nhật `pipeline/docs/runtime/DEBATE_LOG.md`, `STATUS.md`, và `PROGRESS_LOG.md`.

### [2026-08-26 22:09] — Re-Verification Pass & Status Synchronization
- **Task ID:** TASK-004
- **Hành động:**
  - Đã đọc kỹ lại `pipeline/docs/runtime/DEBATE_LOG.md` và xác nhận tất cả các vấn đề CRITICAL & HIGH đã được giải quyết triệt để.
  - Thực thi lại lệnh `python3 pipeline/scripts/verify.py` kiểm định Tier 1 (Ruff, Mypy, Bandit, Pytest): **PASS 100%**.
  - Đồng bộ và cập nhật các file trạng thái hệ thống: `STATUS.md`, `PROGRESS_LOG.md`, `DEBATE_LOG.md`.
  - Sẵn sàng gửi lại yêu cầu review cho Reviewer Model.

### [2026-08-27 12:17] — Hoàn thành TASK-005
- **Task ID:** TASK-005 (Refactor Decoupled 3-Tier Prompt System for All 9 Personas)
- **Hành động:**
  - Tạo `app/data/persona_definitions.json` chứa định dạng JSON chuẩn cho cả 10 nhân vật (Alex, Lily, Oscar, Viktor, Chanel, Kaelen, Colt, Zarina, Scarlet, Luigi).
  - Refactor `app/characters/__init__.py` nạp động persona definitions từ `app/data/persona_definitions.json` với fallback an toàn.
  - Refactor `app/core/prompt_factory.py` xây dựng hệ thống Decoupled 3-Tier Prompt System (Tier 1: Core Pedagogy & Warmth, Tier 2: Persona Overlay từ JSON, Tier 3: Adaptive CEFR Horizon).
  - Loại bỏ hoàn toàn quy tắc ép `min_words` cứng nhắc và ví dụ mẫu gây lặp câu.
  - Viết unit test suite `tests/test_characters.py` (25 test cases) kiểm tra việc load persona, 3-tier prompt assembly, no min_words rule, và DecoupledPromptFactory. Pass 100% (25/25).
  - Kiểm tra static analysis (Ruff, Mypy) pass 100% không cảnh báo.

### [2026-08-27 12:43] — Hoàn thành TASK-006
- **Task ID:** TASK-006 (Build Structured Topic Bank & Soften Scenario Angles)
- **Hành động:**
  - Khởi tạo và kiểm tra `app/data/topic_bank.json` phân định rõ `free_conversation` (greeting, small talk, hobbies) vs `structured_scenario` (restaurant ordering, job interview, hotel checkin, airport, bargaining, coffee shop).
  - Tích hợp `_load_topic_bank`, `get_topic_info(topic_id)`, `should_enable_scenario_angle(topic_id)` trong `app/core/ai_engine.py`.
  - Cập nhật `start_roleplay_greeting` trong `app/core/ai_engine.py` để chỉ kích hoạt `Dynamic Session Angle` khi `should_enable_scenario_angle` trả về `True` (structured roleplay scenarios). Giữ chủ đề tự do / chào hỏi tự nhiên, không ép kịch bản gượng gạo.
  - Sửa lỗi type annotation `raw_angles` trong `ai_engine.py` cho Mypy compliance.
  - Viết bộ unit test `tests/test_topics.py` (6 test cases) verify topic bank structure, topic info lookup, classification rule, và condition check trong prompt generation. Pass 100%.
  - Chạy static analysis (Ruff, Mypy, Bandit, Pytest) thông qua `python3 pipeline/scripts/verify.py` đạt **PASS 100%**.

### [2026-08-27 13:16] — Hoàn thành TASK-007
- **Task ID:** TASK-007 (Implement Response Rating API & Continuous Feedback Logger)
- **Hành động:**
  - Viết `app/services/feedback_service.py` xử lý việc ghi nhật ký đánh giá vào `app/data/feedback_log.json`, hạ điểm `quality_score` và đưa vào blacklist đối với rating `hollow` / `out_of_context`, tăng điểm hoặc tự động thêm câu thoại mẫu mới đối với rating `good`.
  - Cập nhật `app/core/exemplar_rag.py` để loại bỏ các exemplar bị blacklist hoặc có điểm chất lượng <= 1.0 khỏi kết quả truy xuất RAG.
  - Viết `app/api/feedback_router.py` cung cấp endpoint REST `POST /api/v1/feedback/rate-response` xử lý rating (`hollow`, `out_of_context`, `good`) với Pydantic validation và error status handling.
  - Đăng ký `feedback_router` trong `app/api/routers/__init__.py` và tích hợp vào `app/main.py`.
  - Viết unit test suite `tests/test_feedback.py` (6 test cases) verify API validation, logging, score penalty/blacklist, RAG filtering, boost/auto-addition. Pass 100% (6/6).
  - Chạy `python3 pipeline/scripts/verify.py` kiểm tra Tier 1 (Ruff, Mypy, Bandit, Pytest) đạt **PASS 100%**.

### [2026-08-27 14:53] — Hoàn thành TASK-008
- **Task ID:** TASK-008 (Build Grammar Structure Bank & CEFR Constraint Validator)
- **Hành động:**
  - Tạo `app/data/grammar_bank.json` định nghĩa danh mục cấu trúc ngữ pháp CEFR linh hoạt (`introduced_at_level` và `mastered_at_level`), quy tắc khớp regex patterns, cùng ràng buộc trần số mệnh đề (`max_clauses`) cho từng cấp độ từ Pre-A1 đến C2+ (1-20).
  - Viết module `app/core/grammar_validator.py` triển khai `GrammarValidator` thực hiện:
    1. Ánh xạ CEFR level string/int (1-20) sang rank 0-13 (`get_level_rank`).
    2. Đếm số lượng mệnh đề trong câu và tính số mệnh đề lớn nhất trong phản hồi (`count_clauses`).
    3. Nhận diện các cấu trúc ngữ pháp có trong văn bản thông qua regex pattern matching (`detect_structures`).
    4. Kiểm tra trần cấu trúc ngữ pháp cho phép và trần số mệnh đề theo level target (`validate_grammar`), trả về `GrammarCheckResult`.
  - Viết bộ unit test suite `tests/test_grammar_validator.py` (7 test cases) kiểm tra level rank mapping, clause count algorithm, pattern detection, pass/violate paths, và clause limits. Pass 100% (7/7).
  - Kiểm tra static analysis (Ruff, Mypy, Bandit, Pytest) thông qua `python3 pipeline/scripts/verify.py` đạt **PASS 100%**.
  - Đánh dấu `[x] DONE` cho `TASK-008` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-27 15:02] — Hoàn thành TASK-009
- **Task ID:** TASK-009 (Implement ASR Adaptive Level Detector (IRT Model))
- **Hành động:**
  - Viết module `app/core/adaptive_level_detector.py` phân tích transcript lời nói từ ASR (tốc độ nói WPM, độ dài câu MLU, độ đa dạng từ vựng TTR, mật độ từ đệm filler density, từ vựng nâng cao) để ước lượng năng lực người dùng theo mô hình Item Response Theory (IRT Rasch 1PL/2PL model).
  - Triển khai `ASRFeatureExtractor` để trích xuất các chỉ số ngôn ngữ và tính toán độ khó item ($\beta$).
  - Triển khai `IRTLevelModel` thực hiện chuyển đổi toán học giữa theta $\theta \in [-3.0, +3.0]$, CEFR Level (1-20), mã CEFR ("Pre-A1" đến "C2+"), và IELTS Band (4.0 - 9.0).
  - Triển khai `AdaptiveLevelDetector` quản lý lịch sử rolling turns, cập nhật theta $\theta_{new} = \theta_{old} + \eta(S - P)$, lưu trữ SQLite table `user_adaptive_level`, và phát tín hiệu điều chỉnh độ khó (`increase`, `hold`, `decrease`).
  - Cung cấp hàm tích hợp `get_effective_level` để AI Engine tự động truy vấn level thực tế đo được thay vì dùng level tĩnh.
  - Viết bộ unit test suite `tests/test_adaptive_level.py` (13 test cases) kiểm tra toàn bộ IRT math, feature extraction, level updates, promotion/demotion, và DB persistence. Pass 100% (13/13).
  - Kiểm tra static analysis (Ruff, Mypy, Bandit, Pytest) thông qua `python3 pipeline/scripts/verify.py` đạt **PASS 100%**.
  - Đánh dấu `[x] DONE` cho `TASK-009` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-27 23:17] — Hoàn thành TASK-010
- **Task ID:** TASK-010 (Optimistic Client-Side STT & Asynchronous Acoustic Extraction)
- **Hành động:**
  - Cập nhật `app/api/routers/audio.py` bổ sung endpoint `POST /api/audio/extract_acoustic_metrics` xử lý trích xuất chỉ số âm học (WPM, ngập ngừng/pauses, pronunciation score, fluency tier) từ audio recorded blob và transcript trong nền.
  - Cập nhật `static/js/speech.js` hỗ trợ **Optimistic Client-Side STT**: ngay khi người dùng dứt lời, transcript từ Web Speech API được gửi tức thì vào `onResult(textToSubmit, true, null)` (~0ms delay), đồng thời tiến trình upload audio webm được đẩy sang kênh bất đồng bộ `_extractAcousticMetricsAsync` mà không gây nghẽn luồng hội thoại.
  - Viết bộ unit & integration test suite `tests/test_optimistic_stt.py` (4 test cases) kiểm tra endpoint acoustic extraction có audio và không có audio, fallback transcribe endpoint, và JavaScript contract alignment trong `speech.js`. Pass 100% (4/4).
  - Kiểm tra static analysis (Ruff, Mypy, Bandit, Pytest) qua `python3 pipeline/scripts/verify.py` đạt **PASS 100%**.
  - Đánh dấu `[x] DONE` cho `TASK-010` trong `pipeline/docs/context/Tasks_list.md`.

### [2026-08-27 23:45] — Hoàn thành TASK-012
- **Task ID:** TASK-012 (Micro-LLM Heuristic Retry Rewriter (Natural Contextual Downgrade))
- **Hành động:**
  - Tạo module `app/core/micro_llm_rewriter.py` triển khai `MicroLLMRewriter` xử lý việc tự động hạ cấp từ vựng/cấu trúc (Contextual Downgrade) một cách tự nhiên trong <150ms khi phát hiện vi phạm trần CEFR level.
  - Tích hợp từ điển `HEURISTIC_DOWNGRADE_MAP` thực hiện downgrade từ vựng tự nhiên (ví dụ: `contemplate` -> `think about`, `philosophical` -> `big`, `deeply` -> `a lot`) khi LLM APIs không khả dụng/offline, đồng thời đảm bảo bảo toàn cấu trúc câu và luôn kết thúc bằng một câu hỏi mở (`OPEN-ENDED QUESTION`).
  - Tích hợp `MicroLLMRewriter` vào `AIEngine._call_llm_with_heuristic_loop` trong `app/core/ai_engine.py` để thay thế việc retry lại toàn bộ prompt hệ thống nặng bằng việc rewrite tập trung vào các từ vi phạm.
  - Cập nhật metadata `heuristic_check` trả về bổ sung `rewritten_by_micro_llm: True`.
  - Viết bộ unit test suite `tests/test_micro_llm_rewriter.py` (4 test cases) kiểm định:
    1. Lowering violating words qua heuristic downgrade map.
    2. Fallback mode khi không có LLM.
    3. Micro-LLM mode qua fast LLM calls.
    4. Tích hợp `AIEngine._call_llm_with_heuristic_loop` với `MicroLLMRewriter`. Pass 100% (4/4).
  - Kiểm tra static analysis (Ruff, Mypy, Bandit, Pytest) qua `python3 pipeline/scripts/verify.py` đạt **PASS 100%**.
  - Đánh dấu `[x] DONE` cho `TASK-012` trong `pipeline/docs/context/Tasks_list.md`.



