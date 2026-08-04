# 🤖 AGENTS.md — Agent Execution Directives & Harness Rules

This document defines the non-negotiable behavioral boundaries and operating instructions for all AI coding agents (Claude Code, Codex, Cursor, Antigravity, etc.) working in the **Duolingo Speak** repository.

---

## 1. Core Directives (*Tips 1, 7, 28*)

1. **You Make the Decisions, AI Executes (*Tip 1*):**
   * The human engineer owns system architecture, API schemas, design tokens, and product decisions.
   * Do **not** invent new frameworks, libraries, or architectural patterns unless explicitly requested in `docs/specs.md`.
   * Follow the existing Duolingo UI/UX tokens and FastAPI backend structures documented in [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md).

2. **Choose Your Shipping Mode (*Tip 28*):**
   * **Interactive Pair Mode:** Communicate concisely, present implementation plans for major changes, and ask clarifying questions for ambiguous user intent.
   * **Autonomous Loop Mode (`Ralph Loop`):** Do not ask questions. Execute the single target item from [`docs/specs.md`], run verification, update [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md), commit changes, or pull the handbrake (`docs/BLOCKED.md`).

3. **Smarter With Every Repetition (*Tip 7*):**
   * If you discover a recurring bug, confusing pattern, or friction point during execution, fix the root cause and document the lesson in [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md) or [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md).

---

## 2. Context & Session Hygiene (*Tips 8, 9, 15*)

1. **Never Compact Your Chat (*Tip 8*):**
   * Summarizing or compacting long conversation histories degrades agent reasoning and introduces hallucinations.
   * If context window limits approach, commit your progress, update the relevant `.md` file, and terminate the session.

2. **One Item, One Fresh Chat (*Tip 15*):**
   * Pick **one** uncompleted checkbox item (`[ ]` -> `[/]`) from [`docs/specs.md`] or [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md).
   * Complete the item, verify it, mark it done (`[x]`), and finish your turn.
   * Never bundle multiple independent spec items into a single chat session.

3. **Spawn Helper Agents (*Tip 9*):**
   * Use subagents for parallel research, codebase searching, or code reviews.
   * Never assume a feature is missing without using search tools (`grep_search`, `list_dir`) across `app/` and `static/`.

---

## 3. Error Handling & Loop Recovery (*Tips 11, 16, 18, 19*)

1. **Fix a Bug Older Than You (*Tip 11*):**
   * Before modifying code to fix an issue, trace the Git history and verify if the issue is a legacy limitation or intentional constraint.
   * Check [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md) before refactoring legacy components.

2. **The `BLOCKED.md` Handbrake (*Tip 16*):**
   * If you encounter an unresolvable error (e.g., missing API key, broken third-party dependency, contradictory specs) after 2 reasonable attempts, **STOP**.
   * Document the exact error, command output, and context in [`docs/BLOCKED.md`].
   * Do **not** spin in infinite retry loops or apply hacky workarounds that degrade codebase health.

3. **Recover With Git Reset (*Tip 18*):**
   * In automated loop executions, if verification tests fail after an implementation attempt, use `git reset --hard HEAD` to restore a clean state before attempting a revised approach.

4. **Exit Codes for Every Ending (*Tip 19*):**
   * Ensure any scripts, validation hooks, or loop runners return exit code `0` on success and non-zero (`1` for failure, `2` for blocked) on exit.

---
---

# [VI] 🤖 AGENTS.md — Chỉ Thị Thực Thi & Quy Tắc Harness Cho AI Agent

Tài liệu này xác định các ranh giới hành vi không thể thương lượng và hướng dẫn hoạt động cho tất cả các AI coding agent (Claude Code, Codex, Cursor, Antigravity, v.v.) làm việc trong kho lưu trữ **Duolingo Speak**.

---

## 1. Chỉ Thị Cốt Lõi (*Tips 1, 7, 28*)

1. **Con Người Đưa Ra Quyết Định, AI Thực Thi (*Tip 1*):**
   * Kỹ sư con người là người quyết định kiến trúc hệ thống, cấu trúc API, design token và sản phẩm.
   * **Không** tự ý sáng tạo ra framework, thư viện hoặc mô hình kiến trúc mới trừ khi được yêu cầu rõ ràng trong `docs/specs.md`.
   * Tuân thủ đúng phong cách UI/UX Duolingo và cấu trúc backend FastAPI đã được tài liệu hóa tại [`docs/architecture.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/architecture.md).

2. **Chọn Chế Độ Vận Hành (*Tip 28*):**
   * **Chế độ Lập trình Cặp Tương tác (Interactive Pair Mode):** Giao tiếp súc tích, trình bày kế hoạch triển khai cho các thay đổi lớn, và đặt câu hỏi làm rõ khi yêu cầu của người dùng chưa rõ ràng.
   * **Chế độ Vòng lặp Tự động (Autonomous Loop Mode - `Ralph Loop`):** Không đặt câu hỏi. Thực thi đúng mục tiêu đơn lẻ từ [`docs/specs.md`], chạy kiểm thử, cập nhật [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md), commit thay đổi hoặc kích hoạt phanh khẩn cấp (`docs/BLOCKED.md`).

3. **Thông Minh Hơn Sau Mỗi Lần Lặp (*Tip 7*):**
   * Nếu phát hiện lỗi lặp đi lặp lại, mô hình gây nhầm lẫn hoặc điểm nghẽn trong quá trình thực thi, hãy sửa gốc rễ vấn đề và ghi chép lại bài học vào [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md) hoặc [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md).

---

## 2. Vệ Sinh Ngữ Cảnh & Phiên Làm Việc (*Tips 8, 9, 15*)

1. **Không Bao Giờ Nén Lịch Sử Trò Chuyện (*Tip 8*):**
   * Việc tóm tắt hoặc nén lịch sử trò chuyện dài làm giảm khả năng suy luận của agent và gây ra hiện tượng ảo giác (hallucination).
   * Nếu gần đạt tới giới hạn cửa sổ ngữ cảnh, hãy commit công việc hiện tại, cập nhật tài liệu `.md` tương ứng và kết thúc phiên làm việc.

2. **Một Mục, Một Phiên Mới (*Tip 15*):**
   * Chọn **một** mục chưa hoàn thành (`[ ]` -> `[/]`) từ [`docs/specs.md`] hoặc [`docs/WORK_BOARD.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/WORK_BOARD.md).
   * Hoàn thành mục đó, kiểm thử xác nhận, đánh dấu hoàn thành (`[x]`), và kết thúc lượt thực thi.
   * Không bao giờ gộp nhiều mục spec độc lập vào một phiên trò chuyện duy nhất.

3. **Tạo Các Agent Phụ Trợ (*Tip 9*):**
   * Sử dụng subagent để tìm kiếm song song trong codebase, nghiên cứu kỹ thuật hoặc review code.
   * Không bao giờ giả định một tính năng chưa được xây dựng mà không dùng công cụ tìm kiếm (`grep_search`, `list_dir`) trên toàn bộ thư mục `app/` và `static/`.

---

## 3. Xử Lý Lỗi & Phục Hồi Vòng Lặp (*Tips 11, 16, 18, 19*)

1. **Sửa Lỗi Lâu Đời Hơn Bạn (*Tip 11*):**
   * Trước khi sửa một vấn đề cũ trong code, hãy tra cứu lịch sử Git để kiểm tra xem đó là giới hạn từ trước hay là ràng buộc có chủ ý.
   * Kiểm tra [`docs/TECH_DEBT.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/TECH_DEBT.md) trước khi tái cấu trúc các thành phần cũ.

2. **Phanh Khẩn Cấp `BLOCKED.md` (*Tip 16*):**
   * Nếu gặp phải một lỗi không thể tự giải quyết (ví dụ: thiếu API key, thư viện bên thứ ba bị lỗi, spec mâu thuẫn) sau 2 lần thử hợp lý, **HÃY DỪNG LẠI**.
   * Ghi chép chi tiết lỗi, đầu ra lệnh và bối cảnh vào [`docs/BLOCKED.md`].
   * **Không** mắc kẹt trong vòng lặp thử lại vô hạn hoặc áp dụng các thủ thuật tạm bợ làm giảm chất lượng code.

3. **Phục Hồi Với Git Reset (*Tip 18*):**
   * Trong các vòng lặp tự động, nếu kiểm thử thất bại sau một nỗ lực triển khai, hãy sử dụng `git reset --hard HEAD` để khôi phục trạng thái sạch trước khi thử giải pháp mới.

4. **Mã Thoát Cho Mọi Kết Thúc (*Tip 19*):**
   * Đảm bảo mọi tập tin script, kiểm thử xác nhận hoặc trình chạy vòng lặp trả về mã thoát `0` khi thành công và khác 0 (`1` khi thất bại, `2` khi bị block).
