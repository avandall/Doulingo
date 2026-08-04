# 📜 docs/rules.md — Coding Standards & Design Token Rules (Generic Template)

> This document defines coding standards, design rules, and commit message structures for the repository.

---

## 1. Coding & Type Standards (*Tip 2*)
- **Clean Code & Type Safety:** Always provide explicit types/type-hints for function parameters and return values.
- **Docstrings & Comments:** Explain the *why*, not just the *what*.
- **No Silent Failures:** Always catch and log specific errors rather than using generic error swallowing.
- **Mandatory Auto-Logging & Self-QA (*Tip 24*):**
  - **Auto-Logging:** All new logic functions and API endpoints MUST use structured logging (`logger.info` for critical inputs/outputs, and `logger.error(..., exc_info=True)` for exceptions). Never swallow errors silently.
  - **Self-QA with Chrome DevTools MCP:** In automated execution loops (such as the Ralph Loop), after modifying code, the agent MUST act as QA by: (1) Running a background test server, (2) Calling `chrome-devtools-mcp` tools (`navigate_to_url`, `click_element`, `get_console_logs`) to verify the UI/API in a real browser, and (3) Verifying zero JavaScript Console errors and clean HTTP 200/201 logs before committing.
  - **Log Size & Subagent Extraction Warning:**
    > [!WARNING]
    > Before reading log files or console output directly into your context, always inspect the size of the log first. If the log is large, spawn a helper subagent (*Tip 9*) to parse, filter, and extract ONLY the relevant error tracebacks or snippets that matter, returning just the condensed summary to the main agent.

---

## 2. Design Tokens & UI/UX Standards (*Tip 1, 25*)
- **Design Tokens:** Define and use standardized CSS variables or theme constants for colors, spacing, and border-radius.
- **Consistent Layouts:** Never use ad-hoc inline styles. Use the defined component system.

---

## 3. Git Commit Standards (*Tip 10*)
All commit messages must follow standard Conventional Commits:
```
<type>(<scope>): <summary>

- Why: <Explanation of the root cause or reason for the change>
- What: <Specific files and functions modified>
- Verification: <Commands run to test and verify the change>
```
Valid types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

---
---

# [VI] 📜 docs/rules.md — Tiêu Chuẩn Lập Trình & Token Thiết Kế (Mẫu Dùng Chung)

> Tài liệu này định nghĩa các tiêu chuẩn viết code, quy tắc thiết kế và cấu trúc commit cho kho lưu trữ.

---

## 1. Tiêu Chuẩn Lập Trình & Kiểu Dữ Liệu (*Tip 2*)
- **Code Sạch & An Toàn Kiểu:** Luôn khai báo rõ ràng kiểu dữ liệu cho tham số hàm và giá trị trả về.
- **Docstring & Chú Thích:** Giải thích *tại sao (why)* thay vì chỉ ghi *cái gì (what)*.
- **Không Để Xảy Lỗi Ngầm:** Luôn bắt và log cụ thể từng lỗi thay vì nuốt lỗi chung chung.
- **Bắt Buộc Tự Động Viết Log & Tự Kiểm Thử QA (*Tip 24*):**
  - **Tự Động Viết Log:** Mọi hàm xử lý logic và API endpoint mới BẮT BUỘC phải ghi log có cấu trúc (`logger.info` cho dữ liệu đầu vào/đầu ra quan trọng, và `logger.error(..., exc_info=True)` khi bắt exception). Không bao giờ nuốt lỗi ngầm.
  - **Tự Kiểm Thử QA bằng Chrome DevTools MCP:** Trong vòng lặp tự động (như Ralph Loop), sau khi code xong, Agent BẮT BUỘC phải đóng vai trò QA bằng cách: (1) Khởi chạy máy chủ thử nghiệm nền, (2) Gọi các công cụ của `chrome-devtools-mcp` (`navigate_to_url`, `click_element`, `get_console_logs`) để kiểm thử UI/API trên trình duyệt thực, và (3) Xác nhận Console trình duyệt không có lỗi JavaScript và log server trả về HTTP 200/201 sạch sẽ trước khi commit.
  - **Cảnh Báo Kích Thước Log & Lọc Bằng Subagent:**
    > [!WARNING]
    > Trước khi đọc trực tiếp file log hoặc đầu ra console vào ngữ cảnh, luôn kiểm tra kích thước của log trước. Nếu log quá lớn, hãy khởi tạo một subagent phụ trợ (*Tip 9*) để lọc, phân tích và chỉ trích xuất những phần traceback hoặc lỗi thực sự quan trọng rồi trả về cho main agent, tránh làm tràn bộ nhớ ngữ cảnh.

---

## 2. Token Thiết Kế & Tiêu Chuẩn UI/UX (*Tip 1, 25*)
- **Design Tokens:** Định nghĩa và sử dụng các biến CSS chuẩn cho màu sắc, khoảng cách và độ bo góc.
- **Bố Cục Nhất Quán:** Không sử dụng inline styles tùy tiện. Sử dụng đúng hệ thống component đã định nghĩa.

---

## 3. Tiêu Chuẩn Git Commit (*Tip 10*)
Mọi commit message phải tuân theo chuẩn Conventional Commits:
```
<type>(<scope>): <summary>

- Why: <Giải thích nguyên nhân gốc rễ hoặc lý do của thay đổi>
- What: <Các file và hàm cụ thể được chỉnh sửa>
- Verification: <Các lệnh đã chạy để kiểm thử và xác nhận thay đổi>
```
Các type hợp lệ: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
