# 🛑 docs/BLOCKED.md — The Autonomous Handbrake Log

This file acts as the emergency handbrake for AI agents and automated coding loops (*Tip 16: The BLOCKED.md Handbrake*; *Tip 19: Exit Codes for Every Ending*).

---

## 🛑 How to Use This Handbrake

1. If an agent or script encounters an unresolvable error after **2 retry attempts** (e.g., missing API key, broken third-party dependency, contradictory specifications), it **MUST NOT** guess or enter an infinite loop.
2. Record the blocker details in the ledger below.
3. Terminate the session or loop with **Exit Code `2`** (`BLOCKED`).
4. A human supervisor or reviewer agent must inspect and resolve the blocker before the item can be retried.

---

## 📋 Active & Historical Blockers Ledger

| Date | Agent / Loop ID | Spec Item / Target File | Error Description & Command Output | Status | Resolved By |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *Example* | `Ralph-Loop-01` | `tts_service.py` | `edge-tts API connection timeout after 30s` | `RESOLVED` | Added `gTTS` fallback mechanism |
| | | | | | |

---

## 🔓 Resolution Workflow for Engineers

1. Review the error description in the table above.
2. Fix the underlying dependency, API credential in `.env`, or requirement in [`docs/specs.md`].
3. Update the item's Status from `BLOCKED` to `RESOLVED`.
4. Re-run the target spec item in a **fresh chat session** (*Tip 15*).

---
---

# [VI] 🛑 docs/BLOCKED.md — Nhật Ký Phanh Khẩn Cấp Tự Động

Tập tin này đóng vai trò là chiếc phanh khẩn cấp cho AI agent và các vòng lặp lập trình tự động (*Tip 16: The BLOCKED.md Handbrake*; *Tip 19: Exit Codes for Every Ending*).

---

## 🛑 Hướng Dẫn Sử Dụng Phanh Khẩn Cấp

1. Nếu agent hoặc script gặp phải một lỗi không thể giải quyết sau **2 lần thử** (ví dụ: thiếu API key, thư viện bên thứ ba hỏng, đặc tả mâu thuẫn), agent **KHÔNG ĐƯỢC** đoán mò hay chạy vòng lặp vô hạn.
2. Ghi chép chi tiết nguyên nhân cản trở vào bảng nhật ký bên dưới.
3. Kết thúc phiên hoặc trình lặp với **Mã Thoát `2`** (`BLOCKED`).
4. Kỹ sư giám sát hoặc reviewer agent phải kiểm tra và khắc phục điểm cản trở trước khi tính năng này có thể được chạy tiếp.

---

## 📋 Bảng Theo Dõi Các Điểm Cản Trở Hiện Tại & Lịch Sử

| Ngày | ID Agent / Vòng Lặp | Mục Spec / Tập Tin Đích | Mô Tả Lỗi & Đầu Ra Lệnh | Trạng Thái | Người Xử Lý |
| :--- | :--- | :--- | :--- | :--- | :--- |
| *Ví dụ* | `Ralph-Loop-01` | `tts_service.py` | `edge-tts API connection timeout after 30s` | `RESOLVED` | Thêm cơ chế chuyển xuống gTTS dự phòng |
| | | | | | |

---

## 🔓 Quy Trình Khắc Phục Cho Kỹ Sư

1. Đọc chi tiết mô tả lỗi trong bảng trên.
2. Sửa lỗi thư viện, thông tin xác thực API trong `.env`, hoặc làm rõ yêu cầu trong [`docs/specs.md`].
3. Cập nhật Trạng Thái của mục từ `BLOCKED` sang `RESOLVED`.
4. Chạy lại mục spec đó trong **một phiên trò chuyện mới hoàn toàn** (*Tip 15*).
