# 🔁 docs/RALPH_LOOP.md — The Autonomous Build-Test-Fix Manual

This manual defines the operational guidelines for running **The Ralph Loop** — the autonomous build-test-fix cycle in the **Duolingo Speak** repository (*Tip 17: Automate It All: The Ralph Loop*).

---

## 1. What is The Ralph Loop? (*Tip 17*)

The Ralph Loop is a structured, autonomous workflow pattern where an AI coding agent executes tasks from [`docs/specs.md`] unattended while maintaining strict quality and error boundaries.

```mermaid
graph TD
    A[Start Fresh Chat Session - Tip 15] --> B[Read AGENTS.md & docs/rules.md]
    B --> C[Pick 1 Unfinished Item from docs/specs.md]
    C --> D[Implement Logical Unit - Tip 14]
    D --> E{Run Verification Tests}
    E -->|Success| F[Commit with Structured Message - Tip 10]
    F --> G[Mark Spec Checkbox [x] & Update WORK_BOARD.md]
    G --> H[Exit Code 0: SUCCESS]
    E -->|Failure - Attempt 1| I[Analyze Error & Retry Fix]
    I --> D
    E -->|Failure - Attempt 2| J[git reset --hard HEAD - Tip 18]
    J --> K[Log Error to docs/BLOCKED.md - Tip 16]
    K --> L[Exit Code 2: BLOCKED - Tip 19]
```

---

## 2. Core Execution Disciplines

### 2.1 Recover With Git Reset (*Tip 18*)
* If an implementation attempt breaks automated tests or introduces syntax errors that cannot be cleanly resolved on the second retry, execute `git reset --hard HEAD`.
* Never let an agent pile speculative fixes on top of broken code.

### 2.2 Exit Codes for Every Ending (*Tip 19*)
All scripts and loop runners must terminate with standard exit codes:
* **`0` (`SUCCESS`)**: Spec item implemented, verified, and committed.
* **`1` (`RETRY_NEEDED`)**: Non-critical verification failure; loop runner may spawn a fresh attempt.
* **`2` (`BLOCKED`)**: Handbrake pulled; logged to [`docs/BLOCKED.md`]. Needs human engineer intervention.

### 2.3 Log Every Iteration (*Tip 20, 24*)
* Every iteration of the Ralph Loop must append an execution entry to an iteration log or emit real-time streaming logs (*Tip 24: Close the Loop With Live Logs*).
* Include: Timestamp, Target Spec Item, Test Commands Run, Exit Code, and Git Commit Hash (if successful).

---

## 3. Self-Improving Harness (*Tip 21, 22, 23*)

1. **Improve the Loop From Inside (*Tip 21*):**
   * If an agent in the loop detects repeated friction (e.g., an outdated docstring, confusing API schema, or missing Duolingo CSS token), it is authorized to propose a documentation improvement in [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md).
2. **Loop Everything Repetitive (*Tip 22*):**
   * Automate repetitive QA checks (e.g., checking all 20 CEFR level configurations in `app/ai_engine.py` or verifying PWA asset loading) via scripts and scheduled agent runs.
3. **Climb One Level at a Time (*Tip 23*):**
   * Only add new automation scripts or custom tools after the base loop executes reliably without false positives.

---

## 4. Bash Script Template & New Project Setup Guide

### 4.1 Bash Script Template (`ralph_loop.sh`)
To run an autonomous overnight loop, place this script in your project root and execute `chmod +x ralph_loop.sh`:

```bash
#!/usr/bin/env bash
# ralph_loop.sh — Autonomous Build-Test-Fix Loop Runner

MAX_ITERATIONS=10
ITERATION=0

echo "🚀 [Ralph Loop] Starting autonomous coding loop (Max iterations: $MAX_ITERATIONS)..."

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  ITERATION=$((ITERATION + 1))
  echo "🔄 [Ralph Loop] Iteration #$ITERATION starting..."

  # 1. Check if there are any remaining unfinished items '[ ]' in docs/specs.md
  if ! grep -q "\[ \]" docs/specs.md; then
    echo "🎉 [Ralph Loop] No remaining '[ ]' items found in docs/specs.md. All tasks completed!"
    exit 0
  fi

  # 2. Invoke AI Agent CLI in autonomous non-interactive mode
  # Replace 'ai-agent-cli' with your CLI tool (e.g., claude, cursor-cli, or custom LLM agent):
  ai-agent-cli --non-interactive --prompt "
    Read AGENTS.md and docs/rules.md.
    Open docs/specs.md and pick EXACTLY ONE unfinished item '[ ]'.
    Change its status to '[/]' and update docs/WORK_BOARD.md.
    Implement the logical unit and run automated verification tests.
    If tests pass:
      1. Commit changes using conventional commit format.
      2. Mark item '[x]' in docs/specs.md and 'DONE' in docs/WORK_BOARD.md.
      3. Exit with code 0.
    If tests fail after 2 attempts:
      1. Run 'git reset --hard HEAD'.
      2. Log error details in docs/BLOCKED.md.
      3. Exit with code 2.
  "

  EXIT_CODE=$?

  if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ [Ralph Loop] Iteration #$ITERATION succeeded! Proceeding to next item..."
  elif [ $EXIT_CODE -eq 2 ]; then
    echo "🛑 [Ralph Loop] HANDBRAKE PULLED (Exit code 2). Check docs/BLOCKED.md!"
    exit 2
  else
    echo "⚠️ [Ralph Loop] Iteration #$ITERATION failed (Exit code $EXIT_CODE). Retrying next loop..."
  fi

  sleep 2
done
```

### 4.2 How to Setup a New Project for Ralph Loop
1. **Required Docs Hub Location**:
   * Put `README.md` and `AGENTS.md` in the **project root directory** (`/`).
   * Put `rules.md`, `architecture.md`, `specs.md`, `BLOCKED.md`, `WORK_BOARD.md`, and `TECH_DEBT.md` in `/docs/`.
2. **AI Agent Setup & Configuration**:
   * Ensure your project has **automated test CLI commands** (e.g., `pytest`, `npm test`, or an API validation script). The loop relies on test exit codes (`0`, `1`, `2`) to verify success.
   * Configure your AI CLI tool to run headless/non-interactive and give it file edit + bash execution permissions.

---
---

# [VI] 🔁 docs/RALPH_LOOP.md — Cẩm Nang Vòng Lặp Build-Test-Fix Tự Động

Tài liệu này định nghĩa các nguyên tắc vận hành cho **The Ralph Loop** — chu trình build-test-fix tự động trong kho lưu trữ **Duolingo Speak** (*Tip 17: Automate It All: The Ralph Loop*).

---

## 1. The Ralph Loop Là Gì? (*Tip 17*)

Ralph Loop là một mô hình quy trình tự động có cấu trúc, trong đó AI coding agent tự động thực thi các tác vụ từ [`docs/specs.md`] mà không cần can thiệp liên tục, đồng thời giữ vững các giới hạn kiểm thử và xử lý lỗi.

```mermaid
graph TD
    A[Mở Phiên Chat Mới Hoàn Toàn - Tip 15] --> B[Đọc AGENTS.md & docs/rules.md]
    B --> C[Chọn 1 Mục Chưa Xong Từ docs/specs.md]
    C --> D[Triển Khai Đơn Vị Logic - Tip 14]
    D --> E{Chạy Kiểm Thử Xác Nhận}
    E -->|Thành công| F[Commit Với Message Chuẩn - Tip 10]
    F --> G[Đánh Dấu Checkbox [x] & Cập Nhật WORK_BOARD.md]
    G --> H[Mã Thoát 0: THÀNH CÔNG]
    E -->|Thất bại - Lần 1| I[Phân Tích Lỗi & Thử Sửa]
    I --> D
    E -->|Thất bại - Lần 2| J[git reset --hard HEAD - Tip 18]
    J --> K[Ghi Nhật Ký Vào docs/BLOCKED.md - Tip 16]
    K --> L[Mã Thoát 2: BỊ CẢN TRỞ - Tip 19]
```

---

## 2. Các Kỷ Luật Thực Thi Cốt Lõi

### 2.1 Phục Hồi Với Git Reset (*Tip 18*)
* Nếu một nỗ lực triển khai làm hỏng kiểm thử tự động hoặc gây lỗi cú pháp mà không thể sửa gọn gàng trong lần thử thứ hai, hãy thực hiện lệnh `git reset --hard HEAD`.
* Không bao giờ để agent chồng chất các bản vá lỗi suy đoán lên trên đoạn code hỏng.

### 2.2 Mã Thoát Cho Mọi Kết Thúc (*Tip 19*)
Tất cả các script và trình lặp tự động phải kết thúc bằng mã thoát tiêu chuẩn:
* **`0` (`SUCCESS` - Thành Công)**: Mục spec đã được triển khai, kiểm thử xác nhận và commit thành công.
* **`1` (`RETRY_NEEDED` - Cần Thử Lại)**: Lỗi kiểm thử không nghiêm trọng; trình điều khiển có thể tạo phiên mới để thử lại.
* **`2` (`BLOCKED` - Bị Cản Trở)**: Phanh khẩn cấp đã được kéo; ghi nhật ký vào [`docs/BLOCKED.md`]. Cần kỹ sư con người can thiệp.

### 2.3 Ghi Log Từng Lần Lặp (*Tip 20, 24*)
* Mỗi lần lặp của Ralph Loop phải ghi lại một mục vào nhật ký thực thi hoặc xuất log luồng trực tiếp (*Tip 24: Close the Loop With Live Logs*).
* Nội dung log bao gồm: Mốc thời gian, Mục Spec mục tiêu, Lệnh kiểm thử đã chạy, Mã thoát và Mã Hash Commit (nếu thành công).

---

## 3. Hệ Thống Harness Tự Hoàn Thiện (*Tip 21, 22, 23*)

1. **Cải Tiến Vòng Lặp Từ Bên Trong (*Tip 21*):**
   * Nếu agent trong vòng lặp phát hiện điểm nghẽn lặp đi lặp lại (ví dụ: docstring lỗi thời, schema API khó hiểu, hoặc thiếu token CSS Duolingo), agent được ủy quyền đề xuất cải tiến tài liệu trong [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md).
2. **Tự Động Hóa Mọi Thao Tác Lặp Lại (*Tip 22*):**
   * Tự động hóa các bài kiểm tra QA lặp đi lặp lại (ví dụ: kiểm tra cấu hình 20 cấp độ CEFR trong `app/ai_engine.py` hoặc tải tài nguyên PWA) thông qua script và các lượt chạy agent định kỳ.
3. **Tiến Từng Bước Một (*Tip 23*):**
   * Chỉ bổ sung các script tự động hóa hoặc công cụ mới sau khi vòng lặp cơ bản đã hoạt động ổn định và tin cậy.

---

## 4. Script Mẫu & Cách Thiết Lập Cho Dự Án Mới

### 4.1 Script Mẫu (`ralph_loop.sh`)
Để chạy vòng lặp tự động qua đêm, đặt script này ở thư mục gốc dự án và chạy `chmod +x ralph_loop.sh`:

```bash
#!/usr/bin/env bash
# ralph_loop.sh — Trình chạy Vòng lặp Build-Test-Fix tự động

MAX_ITERATIONS=10
ITERATION=0

echo "🚀 [Ralph Loop] Khởi chạy vòng lặp tự động (Tối đa: $MAX_ITERATIONS)..."

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  ITERATION=$((ITERATION + 1))
  echo "🔄 [Ralph Loop] Lần lặp #$ITERATION bắt đầu..."

  # 1. Kiểm tra xem còn checkbox ' [ ] ' nào chưa làm trong docs/specs.md không
  if ! grep -q "\[ \]" docs/specs.md; then
    echo "🎉 [Ralph Loop] Không còn mục ' [ ] ' nào trong docs/specs.md. Tất cả task đã hoàn thành!"
    exit 0
  fi

  # 2. Gọi AI Agent CLI ở chế độ tự động non-interactive
  # Thay 'ai-agent-cli' bằng công cụ CLI của bạn (ví dụ: claude, cursor-cli, hoặc custom agent):
  ai-agent-cli --non-interactive --prompt "
    Read AGENTS.md and docs/rules.md.
    Open docs/specs.md and pick EXACTLY ONE unfinished item '[ ]'.
    Change its status to '[/]' and update docs/WORK_BOARD.md.
    Implement the logical unit and run automated verification tests.
    If tests pass:
      1. Commit changes using conventional commit format.
      2. Mark item '[x]' in docs/specs.md and 'DONE' in docs/WORK_BOARD.md.
      3. Exit with code 0.
    If tests fail after 2 attempts:
      1. Run 'git reset --hard HEAD'.
      2. Log error details in docs/BLOCKED.md.
      3. Exit with code 2.
  "

  EXIT_CODE=$?

  if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ [Ralph Loop] Lần lặp #$ITERATION thành công! Đang chuyển sang mục tiếp theo..."
  elif [ $EXIT_CODE -eq 2 ]; then
    echo "🛑 [Ralph Loop] PHANH KHẨN CẤP ĐÃ KÉO (Exit code 2). Kiểm tra ngay docs/BLOCKED.md!"
    exit 2
  else
    echo "⚠️ [Ralph Loop] Lần lặp #$ITERATION thất bại (Exit code $EXIT_CODE). Đang thử lại..."
  fi

  sleep 2
done
```

### 4.2 Cách Chuẩn Bị Bộ Docs & Setup Cho Dự Án Mới
1. **Vị Trí Đặt Bộ Docs Chuẩn**:
   * Các file điều phối gốc (`README.md`, `AGENTS.md`) **bắt buộc đặt ở thư mục gốc (`/`)** để mọi AI Agent vừa mở ra là thấy ngay.
   * Toàn bộ tài liệu chuyên sâu (`rules.md`, `architecture.md`, `specs.md`, `WORK_BOARD.md`, `BLOCKED.md`, `TECH_DEBT.md`) đặt gọn trong thư mục **`/docs/`**.
2. **Yêu Cầu Bắt Buộc Về Kiểm Thử (Automated Test Hook)**:
   * Vòng lặp Ralph **không thể hoạt động** nếu dự án thiếu bộ test tự động (ví dụ `pytest`, `jest`, hoặc script CLI kiểm thử API). AI cần một lệnh trả về Exit Code (`0`, `1`, `2`) để tự nhận biết code của mình đúng hay sai.
3. **Cấu Hình AI Agent CLI**:
   * Cấu hình CLI (như Claude Code hoặc Cursor CLI) với quyền chỉnh sửa file (`write_file`) và thực thi terminal (`run_command`) mà không cần hỏi xác nhận thủ công cho từng bước lặp.

---
---

# [VI] 🔁 docs/RALPH_LOOP.md — Cẩm Nang Vòng Lặp Build-Test-Fix Tự Động

Cẩm Nang này định nghĩa các nguyên tắc vận hành cho **The Ralph Loop** — chu trình build-test-fix tự động trong kho lưu trữ **Duolingo Speak** (*Tip 17: Automate It All: The Ralph Loop*).

---

## 1. The Ralph Loop Là Gì? (*Tip 17*)

Ralph Loop là một mô hình quy trình tự động có cấu trúc, trong đó AI coding agent tự động thực thi các tác vụ từ [`docs/specs.md`] mà không cần can thiệp liên tục, đồng thời giữ vững các giới hạn kiểm thử và xử lý lỗi.

```mermaid
graph TD
    A[Mở Phiên Chat Mới Hoàn Toàn - Tip 15] --> B[Đọc AGENTS.md & docs/rules.md]
    B --> C[Chọn 1 Mục Chưa Xong Từ docs/specs.md]
    C --> D[Triển Khai Đơn Vị Logic - Tip 14]
    D --> E{Chạy Kiểm Thử Xác Nhận}
    E -->|Thành công| F[Commit Với Message Chuẩn - Tip 10]
    F --> G[Đánh Dấu Checkbox [x] & Cập Nhật WORK_BOARD.md]
    G --> H[Mã Thoát 0: THÀNH CÔNG]
    E -->|Thất bại - Lần 1| I[Phân Tích Lỗi & Thử Sửa]
    I --> D
    E -->|Thất bại - Lần 2| J[git reset --hard HEAD - Tip 18]
    J --> K[Ghi Nhật Ký Vào docs/BLOCKED.md - Tip 16]
    K --> L[Mã Thoát 2: BỊ CẢN TRỞ - Tip 19]
```

---

## 2. Các Kỷ Luật Thực Thi Cốt Lõi

### 2.1 Phục Hồi Với Git Reset (*Tip 18*)
* Nếu một nỗ lực triển khai làm hỏng kiểm thử tự động hoặc gây lỗi cú pháp mà không thể sửa gọn gàng trong lần thử thứ hai, hãy thực hiện lệnh `git reset --hard HEAD`.
* Không bao giờ để agent chồng chất các bản vá lỗi suy đoán lên trên đoạn code hỏng.

### 2.2 Mã Thoát Cho Mọi Kết Thúc (*Tip 19*)
Tất cả các script và trình lặp tự động phải kết thúc bằng mã thoát tiêu chuẩn:
* **`0` (`SUCCESS` - Thành Công)**: Mục spec đã được triển khai, kiểm thử xác nhận và commit thành công.
* **`1` (`RETRY_NEEDED` - Cần Thử Lại)**: Lỗi kiểm thử không nghiêm trọng; trình điều khiển có thể tạo phiên mới để thử lại.
* **`2` (`BLOCKED` - Bị Cản Trở)**: Phanh khẩn cấp đã được kéo; ghi nhật ký vào [`docs/BLOCKED.md`]. Cần kỹ sư con người can thiệp.

### 2.3 Ghi Log Từng Lần Lặp (*Tip 20, 24*)
* Mỗi lần lặp của Ralph Loop phải ghi lại một mục vào nhật ký thực thi hoặc xuất log luồng trực tiếp (*Tip 24: Close the Loop With Live Logs*).
* Nội dung log bao gồm: Mốc thời gian, Mục Spec mục tiêu, Lệnh kiểm thử đã chạy, Mã thoát và Mã Hash Commit (nếu thành công).

---

## 3. Hệ Thống Harness Tự Hoàn Thiện (*Tip 21, 22, 23*)

1. **Cải Tiến Vòng Lặp Từ Bên Trong (*Tip 21*):**
   * Nếu agent trong vòng lặp phát hiện điểm nghẽn lặp đi lặp lại (ví dụ: docstring lỗi thời, schema API khó hiểu, hoặc thiếu token CSS Duolingo), agent được ủy quyền đề xuất cải tiến tài liệu trong [`docs/rules.md`](file:///home/avandall1999/Projects/Doulingo_speak/docs/rules.md).
2. **Tự Động Hóa Mọi Thao Tác Lặp Lại (*Tip 22*):**
   * Tự động hóa các bài kiểm tra QA lặp đi lặp lại (ví dụ: kiểm tra cấu hình 20 cấp độ CEFR trong `app/ai_engine.py` hoặc tải tài nguyên PWA) thông qua script và các lượt chạy agent định kỳ.
3. **Tiến Từng Bước Một (*Tip 23*):**
   * Chỉ bổ sung các script tự động hóa hoặc công cụ mới sau khi vòng lặp cơ bản đã hoạt động ổn định và tin cậy.
