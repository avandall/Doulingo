# 📐 docs/rules.md — Coding Standards, UI/UX Tokens & Git Discipline

This document defines the technical rules, Duolingo UI/UX design system tokens, and version control discipline for **Duolingo Speak** (*Tips 1, 2, 7, 10, 25*).

---

## 1. Non-Negotiable Coding Standards (*Tip 1, 2*)

1. **Preserve Documentation Integrity:**
   * Never delete or modify existing docstrings or inline comments unless explicitly refactoring the associated code logic.
2. **Type Safety & Schema Validation:**
   * All backend REST endpoints in [`app/main.py`](file:///home/avandall1999/Projects/Doulingo_speak/app/main.py) must use Pydantic `BaseModel` schemas for request and response validation.
   * Python functions must include type annotations (`Dict`, `List`, `Optional`, `Any`).
3. **No Unsafe Global State:**
   * Global in-memory caches (`TRANSLATION_CACHE`, `IPA_CACHE`) must remain deterministic and memory-safe.
   * Do not introduce blocking synchronous calls in `async def` routes; run heavy LLM or network requests in background thread pools if needed.
4. **No Silent Failures:**
   * Always catch API and TTS exceptions gracefully. If an LLM or TTS provider fails, fall back to safe defaults (e.g., fallback translation or `gTTS` audio) without crashing the user session.
5. **Mandatory Auto-Logging & Self-QA (*Tip 24*):**
   * **Auto-Logging:** All new logic functions and API endpoints MUST use structured logging (`logger.info` for critical inputs/outputs, and `logger.error(..., exc_info=True)` for exceptions). Never swallow errors silently.
   * **Self-QA with Chrome DevTools MCP:** In automated execution loops (such as the Ralph Loop), after modifying code, the agent MUST act as QA by: (1) Running a background test server (`uv run uvicorn ... &`), (2) Calling `chrome-devtools-mcp` tools (`navigate_to_url`, `click_element`, `get_console_logs`) to verify the UI/API in a real browser, and (3) Verifying zero JavaScript Console errors and clean HTTP 200/201 logs before committing.
   * **Log Size & Subagent Extraction Warning:**
     > [!WARNING]
     > Before reading log files or console output directly into your context, always inspect the size of the log first. If the log is large, spawn a helper subagent (*Tip 9*) to parse, filter, and extract ONLY the relevant error tracebacks or snippets that matter, returning just the condensed summary to the main agent.

---

## 2. Duolingo UI/UX Design System (*Tip 25: Replicate Websites Like a Pro*)

All UI components and CSS rules in [`static/index.html`](file:///home/avandall1999/Projects/Doulingo_speak/static/index.html) and [`static/css/`](file:///home/avandall1999/Projects/Doulingo_speak/static/css/) must adhere to these tokens:

### 2.1 Color Tokens (Duolingo Palette)
| Token Name | Hex Value | Usage |
| :--- | :--- | :--- |
| `--duo-primary-green` | `#58CC02` | Primary Call-to-Action (CTA), success states, brand accents. |
| `--duo-shadow-green` | `#46A302` | 3D button bottom border / box shadow. |
| `--duo-accent-blue` | `#1CB0F6` | Secondary interactive elements, speech bubble borders. |
| `--duo-accent-yellow` | `#FFC800` | XP rewards, streak counters, celebrations. |
| `--duo-accent-coral` | `#FF4B4B` | Error indicators, pronunciation corrections, handbrakes. |
| `--duo-bg-light` | `#F7F7F7` | Light mode primary background. |
| `--duo-bg-dark` | `#131F24` | Dark mode primary background. |

### 2.2 Feather 3D Buttons & Typography
* **Border Radius:** All primary interactive cards and buttons must use `border-radius: 16px` (or `12px` for compact buttons).
* **3D Button Press Effect:**
  * Normal state: `border-bottom: 4px solid var(--duo-shadow-green);`
  * Active/Click state: `transform: translateY(2px); border-bottom: 2px solid var(--duo-shadow-green);`
* **Typography:** Modern, rounded sans-serif font stack (`'Nunito', 'Open Sans', 'Roboto', sans-serif`). Font weights must be bold (`700` or `800`) for headers and buttons.

### 2.3 Audio-Visual Feedback
* **Instant Gratification:** Play an upbeat "Ding!" sound when a speaking turn is completed successfully.
* **Confetti & Rewards:** Display celebratory animations and XP reward cards when finishing a scenario.
* **Non-Blocking Corrections:** Show pronunciation and grammar tips after the AI replies; never interrupt the user while speaking.

---

## 3. Version Control & Git Commit Discipline (*Tip 10*)

All commits created by AI agents or human developers must follow a structured format explaining **what** changed and **why**:

```text
<type>(<scope>): <short summary in present tense>

- Why: <explain the root cause or goal behind this change>
- What: <list specific modifications made to files>
- Verification: <state which automated or manual tests were run>
```

### Valid Commit Types
* `feat`: New user-facing feature or scenario.
* `fix`: Bug fix or error recovery.
* `docs`: Documentation updates (`docs/*.md`, docstrings).
* `refactor`: Code improvements without behavior changes.
* `test`: Adding or updating tests.
* `perf`: Performance or latency optimizations (e.g., TTS / LLM speedups).

---

## 4. Smarter With Every Repetition (*Tip 7*)

* Whenever a bug is discovered or an agent produces incorrect UI styling or broken API payloads, **do not just fix the code**.
* Add a specific preventive rule to this file (`docs/rules.md`) so future agent iterations never repeat the error.

---
---

# [VI] 📐 docs/rules.md — Tiêu Chuẩn Lập Trình, UI/UX Token & Kỷ Luật Git

Tài liệu này xác định các quy tắc kỹ thuật, token thiết kế UI/UX theo phong cách Duolingo, và kỷ luật quản lý phiên bản cho **Duolingo Speak** (*Tips 1, 2, 7, 10, 25*).

---

## 1. Tiêu Chuẩn Lập Trình Không Thể Thương Lượng (*Tip 1, 2*)

1. **Bảo Vệ Tính Toàn Vẹn Tài Liệu:**
   * Không bao giờ xóa hoặc sửa đổi các chú thích (docstring/comment) hiện có trừ khi bạn đang trực tiếp tái cấu trúc logic đoạn code tương ứng.
2. **An Toàn Kiểu Dữ Liệu & Xác Thực Schema:**
   * Tất cả các endpoint REST backend trong [`app/main.py`](file:///home/avandall1999/Projects/Doulingo_speak/app/main.py) phải sử dụng schema Pydantic `BaseModel` để kiểm tra tính hợp lệ của request và response.
   * Các hàm Python phải được chú thích kiểu dữ liệu đầy đủ (`Dict`, `List`, `Optional`, `Any`).
3. **Không Sử Dụng State Toàn Cục Không An Toàn:**
   * Các bộ nhớ đệm trong RAM (`TRANSLATION_CACHE`, `IPA_CACHE`) phải đảm bảo tính xác định và an toàn bộ nhớ.
   * Không đưa các lời gọi hàm đồng bộ gây nghẽn vào các route `async def`; hãy chạy các tác vụ nặng (LLM, gọi mạng) trong luồng nền nếu cần.
4. **Không Để Xảy Lỗi Ngầm:**
   * Luôn bắt lỗi (exception) khi gọi API và TTS một cách trơn tru. Nếu LLM hoặc TTS gặp sự cố, hãy chuyển sang giải pháp dự phòng an toàn (ví dụ: gTTS hoặc dịch dự phòng) mà không làm ngắt quãng phiên học của người dùng.
5. **Bắt Buộc Tự Động Viết Log & Tự Kiểm Thử QA (*Tip 24*):**
   * **Tự Động Viết Log:** Mọi hàm xử lý logic và API endpoint mới BẮT BUỘC phải ghi log có cấu trúc (`logger.info` cho dữ liệu đầu vào/đầu ra quan trọng, và `logger.error(..., exc_info=True)` khi bắt exception). Không bao giờ nuốt lỗi ngầm.
   * **Tự Kiểm Thử QA bằng Chrome DevTools MCP:** Trong vòng lặp tự động (như Ralph Loop), sau khi code xong, Agent BẮT BUỘC phải đóng vai trò QA bằng cách: (1) Khởi chạy máy chủ thử nghiệm nền (`uv run uvicorn ... &`), (2) Gọi các công cụ của `chrome-devtools-mcp` (`navigate_to_url`, `click_element`, `get_console_logs`) để kiểm thử UI/API trên trình duyệt thực, và (3) Xác nhận Console trình duyệt không có lỗi JavaScript và log server trả về HTTP 200/201 sạch sẽ trước khi commit.
   * **Cảnh Báo Kích Thước Log & Lọc Bằng Subagent:**
     > [!WARNING]
     > Trước khi đọc trực tiếp file log hoặc đầu ra console vào ngữ cảnh, luôn kiểm tra kích thước của log trước. Nếu log quá lớn, hãy khởi tạo một subagent phụ trợ (*Tip 9*) để lọc, phân tích và chỉ trích xuất những phần traceback hoặc lỗi thực sự quan trọng rồi trả về cho main agent, tránh làm tràn bộ nhớ ngữ cảnh.

---

## 2. Hệ Thống Thiết Kế UI/UX Duolingo (*Tip 25: Replicate Websites Like a Pro*)

Tất cả các thành phần UI và quy tắc CSS trong [`static/index.html`](file:///home/avandall1999/Projects/Doulingo_speak/static/index.html) và [`static/css/`](file:///home/avandall1999/Projects/Doulingo_speak/static/css/) phải tuân thủ đúng các token sau:

### 2.1 Bảng Màu Đặc Trưng (Duolingo Palette)
| Tên Token | Mã Hex | Sức Dụng |
| :--- | :--- | :--- |
| `--duo-primary-green` | `#58CC02` | Nút kêu gọi hành động (CTA) chính, trạng thái thành công, màu nhận diện thương hiệu. |
| `--duo-shadow-green` | `#46A302` | Viền dưới nút 3D / hiệu ứng bóng chìm. |
| `--duo-accent-blue` | `#1CB0F6` | Thành phần tương tác phụ, viền khung hội thoại. |
| `--duo-accent-yellow` | `#FFC800` | Phần thưởng XP, số chuỗi streak, huy hiệu ăn mừng. |
| `--duo-accent-coral` | `#FF4B4B` | Chỉ báo lỗi, sửa phát âm, nút phanh khẩn cấp. |
| `--duo-bg-light` | `#F7F7F7` | Màu nền chính chế độ sáng (Light Mode). |
| `--duo-bg-dark` | `#131F24` | Màu nền chính chế độ tối (Dark Mode). |

### 2.2 Nút Bo Góc 3D & Nghệ Thuật Chữ (Typography)
* **Độ Bo Góc:** Tất cả các thẻ và nút bấm tương tác chính phải dùng `border-radius: 16px` (hoặc `12px` cho nút nhỏ gọn).
* **Hiệu Ứng Nhấn Nút 3D:**
  * Trạng thái bình thường: `border-bottom: 4px solid var(--duo-shadow-green);`
  * Trạng thái nhấn (Active/Click): `transform: translateY(2px); border-bottom: 2px solid var(--duo-shadow-green);`
* **Typography:** Bộ phông chữ bo tròn hiện đại (`'Nunito', 'Open Sans', 'Roboto', sans-serif`). Độ dày chữ phải đậm (`700` hoặc `800`) cho tiêu đề và nút bấm.

### 2.3 Phản Hồi Âm Thanh & Hình Ảnh
* **Phần Thưởng Tức Thì:** Phát âm thanh "Ding!" vui tai khi người dùng hoàn thành xuất sắc lượt nói.
* **Confetti & Đổi Thưởng:** Hiển thị hiệu ứng pháo giấy chúc mừng và thẻ điểm XP khi hoàn thành một kịch bản.
* **Sửa Lỗi Không Ngắt Lời:** Hiển thị mẹo sửa ngữ pháp và phát âm sau khi AI phản hồi; không bao giờ ngắt lời khi học viên đang nói.

---

## 3. Quản Lý Phiên Bản & Kỷ Luật Commit Git (*Tip 10*)

Tất cả các commit do AI agent hay lập trình viên tạo ra đều phải tuân thủ đúng định dạng cấu trúc giải thích rõ **cái gì** đã thay đổi và **tại sao**:

```text
<type>(<scope>): <tóm tắt ngắn bằng thì hiện tại>

- Why: <giải thích nguyên nhân gốc rễ hoặc mục tiêu của thay đổi>
- What: <liệt kê các sửa đổi cụ thể trong các tập tin>
- Verification: <nêu rõ các kiểm thử tự động hoặc thủ công đã chạy>
```

### Các Loại Commit Hợp Lệ
* `feat`: Tính năng hoặc kịch bản mới cho người dùng.
* `fix`: Sửa lỗi hoặc phục hồi hệ thống.
* `docs`: Cập nhật tài liệu (`docs/*.md`, docstrings).
* `refactor`: Cải tiến code không làm thay đổi hành vi.
* `test`: Thêm hoặc cập nhật kiểm thử.
* `perf`: Tối ưu hóa hiệu năng hoặc độ trễ (ví dụ: tăng tốc TTS / LLM).

---

## 4. Thông Minh Hơn Sau Mỗi Lần Lặp (*Tip 7*)

* Mỗi khi phát hiện lỗi hoặc agent tạo ra phong cách UI sai lệch hay payload API hỏng, **đừng chỉ sửa code**.
* Hãy thêm một quy tắc phòng ngừa cụ thể vào tập tin này (`docs/rules.md`) để các vòng lặp agent tương lai không bao giờ lặp lại sai lầm đó.
