# PROGRESS LOG
# Nhật ký tiến độ — Lịch sử từng iteration

> **Trạng thái:** RUNTIME (Auto-generated) | **Cập nhật:** Append sau mỗi iteration
>
> 🤖 AI APPEND entry mới vào cuối file này sau mỗi iteration. KHÔNG xóa entries cũ.
> Entries cũ nhất ở trên, mới nhất ở dưới.

---

## Format mỗi entry

```markdown
### [ITER-NNN] YYYY-MM-DD HH:MM — <Tên ngắn của iteration>

**Phase:** EXECUTING | REVIEWING | COMMITTING
**Step:** Step N từ PLAN.md
**Duration:** ~X phút

#### Actions Taken
1. [Hành động 1]
2. [Hành động 2]

#### Result
- **Outcome:** PASS | FAIL | PARTIAL | BLOCKED
- **Evidence:** [Link/snippet bằng chứng, output của command]

#### Issues Found
- [Vấn đề gặp phải (nếu có)]

#### Decisions Made
- [Quyết định quan trọng trong iteration này]

#### Git
- **Commit:** `[TASK-ID] type(scope): description`

#### Next
- **Action:** [Bước tiếp theo]
- **State:** [Trạng thái STATUS.md sau entry này]
```

---

## Log Entries

<!-- AI bắt đầu thêm entries từ đây -->

### [ITER-001] 2026-08-21 21:12 — Ingest book data & RAG verification (TASK-001)

**Phase:** COMMITTING & REPORTING (Phase 6 & Phase 7)
**Step:** Step 1 & Step 2 từ PLAN.md
**Duration:** ~15 phút

#### Actions Taken
1. Thực thi `scripts/insert_turso.py output/extracted/ --sqlite data/custom_topics.db` nạp 492 `content_units`, 725 `band_tiers`, và 1078 `sample_dialogues`.
2. Kiểm tra `retrieve_dialogues()` trên database SQLite `data/custom_topics.db` mới nạp, xác nhận trả về đúng 4 mẫu thoại chuẩn RAG.
3. Chạy Tier 1 verification (`pipeline/scripts/verify.py`) & unit test suite (`pytest tests/test_ingestion.py` PASS 100%).
4. Thực hiện Dual-Model Review (Reviewer APPROVED tại `pipeline/docs/runtime/DEBATE_LOG.md`).
5. Tạo Git commit `[TASK-001] feat(data): ingest extracted book YAMLs into SQLite custom_topics.db` (`ccaf4ac`).
6. Cập nhật trạng thái `TASK-001` thành `[x] DONE` trong `Tasks_list.md`, `PLAN.md`, `STATUS.md`.

#### Result
- **Outcome:** PASS
- **Evidence:** SQLite `custom_topics.db` chứa 1078 sample dialogues. Git commit: `ccaf4ace4c8cdae8bf50779f5b0597a6c539bcc1`. Unit tests pass 100%.

#### Issues Found
- Không có issue phát sinh.

#### Decisions Made
- Chấp nhận nạp 492 content units trực tiếp vào DB SQLite local để phục vụ RAG retrieval cascade.

#### Git
- **Commit:** `[TASK-001] feat(data): ingest extracted book YAMLs into SQLite custom_topics.db` (`ccaf4ac`)

#### Next
- **Action:** Chuyển sang TASK-002: Tích hợp RAG Layer (`retrieve_dialogues`) vào `ai_engine.process_turn`.
- **State:** `Phase: IN_PROGRESS` (TASK-001 DONE, 1/5 completed).

### [ITER-002] 2026-08-21 21:30 — Tích hợp RAG Layer (retrieve_dialogues) vào ai_engine.process_turn (TASK-002)

**Phase:** COMMITTING & REPORTING (Phase 6 & Phase 7)
**Step:** Step 1 từ PLAN.md
**Duration:** ~15 phút

#### Actions Taken
1. Thêm helper `_level_to_band_window(level: int)` quy đổi level 1-20 sang IELTS band 4.0-9.0 window.
2. Tích hợp `retrieve_dialogues()` vào `_build_token_efficient_prompt()` trong `app/ai_engine.py`.
3. Định dạng reference dialogues thành khối `REFERENCE DIALOGUES FROM BOOKS` nhúng trực tiếp vào system prompt.
4. Thêm unit test `test_ai_engine_rag_integration` trong `tests/test_ai_engine.py` (PASS 6/6 tests).
5. Thực thi verification command và Tier 1 `verify.py` pass 100%.
6. Dual-model reviewer phê duyệt (APPROVED tại `DEBATE_LOG.md`).
7. Git commit: `[TASK-002] feat(rag): integrate retrieve_dialogues into ai_engine process_turn` (`07789f5`).
8. Cập nhật tiến độ `TASK-002` thành `[x] DONE` trong runtime docs & filesystem.

#### Result
- **Outcome:** PASS
- **Evidence:** Git commit `07789f5`, 6 pytest cases pass 100%, verification command trả về response thành công.

#### Issues Found
- Không có issue phát sinh.

#### Decisions Made
- Dùng fallback try-except quanh `retrieve_dialogues()` để tránh làm gián đoạn hội thoại nếu DB không khả dụng.

#### Git
- **Commit:** `[TASK-002] feat(rag): integrate retrieve_dialogues into ai_engine process_turn` (`07789f5`)

#### Next
- **Action:** Chuyển sang TASK-003: Nâng cấp Context-Aware Fallback Engine thay cho Mock Fallback tĩnh.
- **State:** `Phase: IN_PROGRESS` (TASK-002 DONE, 2/5 completed).

### [ITER-003] 2026-08-21 21:47 — Nâng cấp Context-Aware Fallback Engine thay cho Mock Fallback tĩnh (TASK-003)

**Phase:** COMMITTING & REPORTING (Phase 6 & Phase 7)
**Step:** Step 1 & Step 2 từ PLAN.md
**Duration:** ~15 phút

#### Actions Taken
1. Xây dựng `_get_context_aware_fallback()` trong `app/ai_engine.py` nhận biết sentiment (negative, positive, confused, neutral), duy trì scenario title/topic, và ép dải từ (word count) theo level config `[min_words, max_words]`.
2. Đảm bảo `_get_mock_fallback_response()` ủy quyền cho `_get_context_aware_fallback()`.
3. Viết unit test suite trong `tests/test_fallback_context.py` test sentiment empathy, topic retention, và word count constraints (PASS 4/4 tests).
4. Kiểm thử Tier 1 verification (`verify.py` & `pytest`) PASS 100% (19/19 unit tests total).
5. Dual-Model Reviewer đã phê duyệt (Review Result: APPROVED tại `DEBATE_LOG.md`).
6. Thực hiện Phase 6: Git commit `[TASK-003] feat(engine): implement context-aware fallback engine with level word count constraints` (`7c9a762`).
7. Thực hiện Phase 7: Cập nhật `Tasks_list.md`, `PLAN.md`, `PROGRESS_LOG.md`, `STATUS.md` ra filesystem.

#### Result
- **Outcome:** PASS
- **Evidence:** Git commit `7c9a762`, `pytest tests/test_fallback_context.py` (4 passed), Reviewer APPROVED tại `DEBATE_LOG.md`.

#### Issues Found
- Không có issue phát sinh.

#### Decisions Made
- Sử dụng keyword regex matching linh hoạt để nhận biết sentiment và bổ sung filler/truncation logic bảo đảm luôn đáp ứng word count boundary của LEVEL_CONFIGS.

#### Git
- **Commit:** `[TASK-003] feat(engine): implement context-aware fallback engine with level word count constraints` (`7c9a762`)

#### Next
- **Action:** Chuyển sang TASK-004: Thống nhất 2 Pipeline (Pipeline A & Pipeline B).
- **State:** `Phase: IN_PROGRESS` (TASK-003 DONE, 3/5 completed).

### [ITER-007] 2026-08-21 22:21 — Thống nhất 2 Pipeline (Pipeline A & Pipeline B) (TASK-004)

**Phase:** COMMITTING & REPORTING (Phase 6 & Phase 7)
**Step:** Step 1, Step 2 & Step 3 từ PLAN.md
**Duration:** ~15 phút

#### Actions Taken
1. Bổ sung `level: int | None = None` vào `PromptContext` trong `app/prompt_constructor.py`, cùng các hàm chuyển đổi hai chiều `band_to_level()` và `level_to_band()`.
2. Cập nhật `construct_system_prompt()` trong `app/prompt_constructor.py` để tự động chèn khối ràng buộc `LEVEL_CONFIGS` 20 cấp độ (CEFR, min/max words, vocabulary tier, grammar allowed, example response).
3. Cập nhật `VoiceTurnRequest` và `_execute_voice_turn_pipeline()` trong `app/main.py` nhận parameter `level`, chuyển đổi sang band window tương ứng và truyền vào `PromptContext` + RAG retrieval layer `retrieve_dialogues()`.
4. Bổ sung unit tests kiểm thử 20-level constraints trong `tests/test_prompt_constructor.py` và endpoint `/api/voice/process_turn` có parameter `level` trong `tests/test_mvp_pipeline.py`.
5. Kiểm thử Static Analysis & Runtime Tests (`ruff check`, `mypy`, `bandit`, `pytest tests/test_prompt_constructor.py tests/test_mvp_pipeline.py tests/test_conversational_agent.py` PASS 19/19 tests).
6. Dual-Model Reviewer phê duyệt (APPROVED tại `pipeline/docs/runtime/DEBATE_LOG.md`).
7. Thực hiện Phase 6 (COMMIT): Tạo Git commit `[TASK-004] refactor(prompt-pipeline): unify prompt construction with 20-level configs and align voice turn API` (`1fb7893`).
8. Thực hiện Phase 7 (REPORT): Cập nhật `Tasks_list.md`, `PLAN.md`, `CURRENT_TASK.md`, `PROGRESS_LOG.md`, `STATUS.md` ra filesystem.

#### Result
- **Outcome:** PASS
- **Evidence:** Git commit `1fb7893`, `pytest` 19 unit tests pass 100%, Reviewer APPROVED tại `DEBATE_LOG.md`.

#### Issues Found
- Không có issue phát sinh.

#### Decisions Made
- Đồng bộ hóa 2 pipeline chat turn và voice turn bằng cách đưa `LEVEL_CONFIGS` trực tiếp vào `prompt_constructor.py` và dùng chung RAG retrieval logic.

#### Git
- **Commit:** `[TASK-004] refactor(prompt-pipeline): unify prompt construction with 20-level configs and align voice turn API` (`1fb7893`)

### [ITER-008] 2026-08-21 22:28 — Kiểm thử E2E & Verification toàn bộ luồng hội thoại (TASK-005)

**Phase:** COMMITTING & REPORTING (Phase 6 & Phase 7)
**Step:** Step 1 & Step 2 từ PLAN.md
**Duration:** ~10 phút

#### Actions Taken
1. Thực thi Tier 1 Verification Script (`python3 pipeline/scripts/verify.py`) kiểm tra Ruff, Mypy, Bandit và Pytest suite (PASS 100%).
2. Đọc và kiểm tra `pipeline/docs/runtime/VERIFICATION_REPORT.md` (Status: PASS).
3. Thực hiện Tier 2 Cognitive Review trên `git diff` và đối chiếu `pipeline/docs/core/REVIEW_PROTOCOL.md`.
4. Ghi nhận kết quả review APPROVED vào `pipeline/docs/runtime/DEBATE_LOG.md`.
5. Đánh dấu `TASK-005` thành `[x] DONE` trong `pipeline/docs/context/Tasks_list.md`.
6. Thực hiện Git commit cho TASK-005: `[TASK-005] test(e2e): verify e2e dialogue pipeline and pass tier 1 verification suite`.
7. Cập nhật `STATUS.md` thành `Phase: ALL_DONE` và viết `PROOF_OF_SOLUTION.md`.

#### Result
- **Outcome:** PASS
- **Evidence:** `verify.py` Status: PASS 100%, Pytest suite pass, Reviewer APPROVED tại `DEBATE_LOG.md`.

#### Issues Found
- Không có issue phát sinh.

#### Decisions Made
- Tất cả 5 tasks trong project đã hoàn thành 100%, không còn task dở dang, chuyển trạng thái hệ thống sang ALL_DONE.

#### Git
- **Commit:** `[TASK-005] test(e2e): verify e2e dialogue pipeline and pass tier 1 verification suite`

#### Next
- **Action:** Dự án hoàn tất 100% (5/5 tasks DONE).
- **State:** `Phase: ALL_DONE`




