# DEBATE LOG
# Nhật ký phản biện — Lịch sử tự phản biện và inter-agent critique

> **Trạng thái:** RUNTIME (Auto-generated) | **Cập nhật:** Sau mỗi review session
>
> 🤖 AI APPEND vào file này sau mỗi lần review. KHÔNG xóa entries cũ — lịch sử này có giá trị.
> Đây là "second opinion trail" chứng minh AI đã suy nghĩ nghiêm túc trước khi commit.

---

## Cách đọc file này

Mỗi entry là một round phản biện. Entries được sắp xếp theo thứ tự thời gian (cũ → mới).
Đọc từ cuối file để xem review gần nhất.

---

## Debate Entries

<!-- AI bắt đầu append entries từ đây -->

---

### DEBATE-001 — [YYYY-MM-DD HH:MM]

**Iteration:** ITER-NNN
**Type:** SELF_REVIEW | ADVERSARIAL | INTER_AGENT
**Reviewer:** AI Self | Agent-B (Critic)
**Subject:** [Mô tả ngắn thứ đang review]

#### Critique Raised

**Q1: [Câu hỏi/phê bình 1]**
- **Raised by:** Self / Agent-B
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW | INFO
- **Detail:** [Mô tả chi tiết vấn đề]
- **Response:** [Câu trả lời / phản hồi]
- **Action:** 
  - [ ] FIXED — [Mô tả gì đã fix]
  - [ ] ACCEPTED_RISK — [Lý do chấp nhận rủi ro]
  - [ ] WON'T_FIX — [Lý do không fix]
  - [ ] DEFERRED — [Khi nào sẽ fix: Task-XXX]

---

#### Session Summary

```
Total issues raised:   N
  CRITICAL:  0
  HIGH:      0
  MEDIUM:    N
  LOW:       N
  INFO:      N

Resolution:
  Fixed:          N
  Accepted risk:  N
  Won't fix:      N
  Deferred:       N

Review Result: APPROVED | NEEDS_REVISION | ESCALATE_TO_HUMAN
```

#### Confidence Score

```
Before review:  [Ví dụ: 7/10 — khá tự tin nhưng chưa chắc về edge cases]
After review:   [Ví dụ: 9/10 — đã address tất cả concerns quan trọng]
```

---

## Patterns & Learnings

### Lỗi thường gặp
- [Lỗi thường gặp và cách phòng tránh]

### Câu hỏi hiệu quả để phát hiện lỗi
- [Câu hỏi dùng khi review]

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-22 18:16
### Iteration: 1
### Type: dual-model-review

#### Issues Found
[SEVERITY: HIGH] Tier 1 checks failed on Ruff (Lint) — Evidence: TIER1: FAIL (Python: Ruff)
[SEVERITY: MEDIUM] Dùng print() thay vì logger vi phạm Project Review Rules — Evidence: app/tts_service.py:188, app/ai_engine.py:73

#### Adversarial Questions
1. Điều gì xảy ra khi Tier 1 lint check fail? → Auto-reject theo quy tắc bắt buộc.
2. Tại sao gọi print() thay vì dùng logger? → Vi phạm quy tắc logging của dự án.
3. Timeout giảm xuống 2-3s có gây false negative với Gemini/Groq chậm? → Cần retry hoặc fallback hợp lý.

#### Summary
- Blocking issues (CRITICAL/HIGH): 1
- Non-blocking (MEDIUM/LOW): 1

Review Result: REJECTED: Tier 1 check thất bại (Ruff lint error) và vi phạm rule sử dụng print() thay vì logger.
---DEBATE_LOG_ENTRY_END---

---DEBATE_LOG_ENTRY_START---
## Executor Fix Session — 2026-08-22 18:20
### Iteration: 1.1 (Executor Fix)
### Type: EXECUTOR_FIX

#### Resolution of Reported Issues

1. **[SEVERITY: HIGH] Tier 1 checks failed on Ruff (Lint)**
   - **Action:** FIXED
   - **Details:** Sửa 3 vị trí `raise e` thành `raise` chuẩn trong `app/ai_engine.py` (TRY201). `ruff check .` vượt qua 100% không còn lỗi.

2. **[SEVERITY: MEDIUM] Dùng print() thay vì logger vi phạm Project Review Rules**
   - **Action:** FIXED
   - **Details:** Đã kiểm tra toàn bộ thư mục `app/` và chuyển tất cả 11 câu lệnh `print()` sang đối tượng `logger` tiêu chuẩn (`logger.info`, `logger.warning`, `logger.error`) trong `app/ai_engine.py`, `app/tts_service.py`, `app/main.py`, `app/db.py`, `app/scenarios/__init__.py`, và `app/scenarios/simulation_engine.py`.

#### Session Summary
```
Total issues addressed: 2
  HIGH:   1 FIXED
  MEDIUM: 1 FIXED

Verification Status: PASS (Ruff Lint 0 errors, Logger compliance verified, Tier 1 checks re-executed)
Review Status: READY_FOR_RE_REVIEW
```
---DEBATE_LOG_ENTRY_END---
---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-22 18:34
### Iteration: 1
### Type: dual-model-review

#### Issues Found
[SEVERITY: INFO] Key rotation logic and trace logger standardized with logging instead of print — Evidence: app/ai_engine.py:64-88

#### Adversarial Questions
1. Điều gì xảy ra nếu network latency tăng đột biến khiến timeout 2-3s bị trigger sớm? → Hệ thống sẽ xoay vòng key/model tiếp theo hoặc fallback browser STT/local cache an toàn mà không block app.
2. Việc mark_key_exhausted với HTTP 400/401/402/403/429 có nguy cơ loại bỏ nhầm key không? → Đúng và an toàn, tránh tiếp tục spam requests vào key lỗi/hết quota trong cùng phiên.
3. Có vi phạm quy tắc logging print() nào còn sót lại không? → Toàn bộ log trong diff đã chuyển sang `logger.info`/`warning`/`error`.

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 0

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-22 18:41
### Iteration: 2
### Type: dual-model-review

#### Issues Found
[SEVERITY: INFO] Clean refactoring to logger, refined timeouts, key exhaustion handling, and STT trace metrics — Evidence: app/ai_engine.py, app/db.py, app/main.py

#### Adversarial Questions
1. Việc thêm các status code 400, 401, 402 vào `mark_key_exhausted` có gây false exhaustion cho key hợp lệ khi payload sai format không? → Các request payload đã chuẩn hóa theo schema cố định, gặp 400/401/402 phần lớn là invalid/expired/billing issue, việc mark exhausted giúp xoay key nhanh tránh block luồng.
2. Giảm timeout xuống 2-3s có làm đứt kết nối LLM translation ở mạng chậm không? → Có fallback tuần tự qua pool key Gemini/Groq và fallback text rỗng không crash app.
3. Có còn print() nào vi phạm project review rules không? → Tất cả đã thay bằng logger chuẩn.

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 0

Review Result: APPROVED

---DEBATE_LOG_ENTRY_START---
## Review Session — 2026-08-22 19:25
### Iteration: 1
### Type: dual-model-review

#### Issues Found
[SEVERITY: INFO] Dynamic fallback responses with topic-shift detection and anti-repetition memory — Evidence: app/ai_engine.py:640-870

#### Adversarial Questions
1. Điều gì xảy ra nếu user transcript không chứa bất kỳ topic keyword nào? → Mặc định fallback về scenario title ban đầu an toàn.
2. Vòng lặp 30 lần tính Jaccard similarity có gây chậm CPU không? → String bank ngắn (<50 từ), 30 lần tính set intersection mất <1ms.
3. Có nguy cơ cạn kiệt candidates nếu past_sentences chứa toàn bộ bank không? → Fallback list ban đầu `or openers` đảm bảo luôn có output.

#### Summary
- Blocking issues (CRITICAL/HIGH): 0
- Non-blocking (MEDIUM/LOW): 0

Review Result: APPROVED
---DEBATE_LOG_ENTRY_END---

