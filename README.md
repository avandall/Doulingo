# 🦉 Duolingo Speak Clone & Autonomous "Ralph Loop" Harness

**Duolingo Speak Clone** là ứng dụng luyện nói tiếng Anh với hội thoại ngữ cảnh dài (Long-Context Roleplay Conversation), mang đậm bản sắc giao diện **Duolingo UI/UX & Gamification DNA**.

Dự án này được tích hợp trọn bộ hệ thống **Harness Engineering (Ralph Loop)** dựa trên triết lý từ video [Harness Engineering: 29 Tips to Build the Systems That Build Software](https://www.youtube.com/watch?v=rraHPF4ZgCw), cho phép AI Agent tự động vận hành qua đêm (Overnight Mode) để hoàn thiện 100% các tính năng.

---

## 🏗️ Hệ Thống Tài Liệu Harness Engineering (`docs/`)

Hệ thống tài liệu là "bộ nhớ" và "dây cương" giúp AI Agent tự động code chính xác theo mô hình **Ralph Loop**:

| Tài liệu | Link file | Mô tả chi tiết |
| :--- | :--- | :--- |
| **Kiến trúc hệ thống** | [architecture.md](file:///home/avandall/project/Doulingo_Speak/Doulingo/docs/architecture.md) | Sơ đồ hệ thống, luồng dữ liệu STT -> LLM -> TTS, màu sắc & nút bấm 3D chuẩn Duolingo. |
| **Quy tắc Agent** | [rules.md](file:///home/avandall/project/Doulingo_Speak/Doulingo/docs/rules.md) | Các nguyên tắc bắt buộc: One Item One Fresh Chat, Don't Describe Code Point To It, Never Compact Chat, Git Reset Recovery. |
| **Backlog Specs** | [specs.md](file:///home/avandall/project/Doulingo_Speak/Doulingo/docs/specs.md) | Danh sách kiểm thử chi tiết (`- [ ]` -> `- [x]`) cho Frontend, Backend, AI Engine và Gamification. |
| **System Prompt** | [prompt.md](file:///home/avandall/project/Doulingo_Speak/Doulingo/docs/prompt.md) | System prompt được đưa vào AI CLI ở mỗi lần lặp (Iteration) của Ralph Loop. |
| **Hướng dẫn qua đêm** | [ralph_loop_guide.md](file:///home/avandall/project/Doulingo_Speak/Doulingo/docs/ralph_loop_guide.md) | Hướng dẫn cấu hình CLI, chạy qua đêm với `tmux`/`nohup` và cơ chế phục hồi tự động. |

---

## 🚀 Hướng Dẫn Chạy Thử "Ralph Loop" Qua Đêm Thành Công 100%

Bạn có **2 cách** để chạy tự động qua đêm tùy theo môi trường làm việc:

### Cách 1: Chạy trực tiếp trong Antigravity IDE (⭐ Khuyên dùng - Không cần cài CLI, Không cần `tmux`)
Vì bạn đang sử dụng **Antigravity IDE**, IDE đã tích hợp sẵn AI Agent.
- **Bước 1:** Vào cài đặt nguồn điện máy tính (Power/Sleep), chọn **Never Sleep** khi cắm sạc.
- **Bước 2:** Nhập lệnh `/goal` vào khung chat của IDE kèm lời nhắc:
  ```
  /goal Hãy thực hiện tuần tự tất cả task chưa hoàn thành (- [ ]) trong docs/specs.md theo đúng triết lý Ralph Loop: đọc docs -> chọn 1 task -> code -> test cú pháp -> cập nhật [x] -> commit. Không dừng lại cho đến khi hoàn thành 100% tất cả checkbox trong docs/specs.md!
  ```
- **Bước 3:** Để máy tự chạy qua đêm. IDE sẽ liên tục lặp lại chu trình cho đến sáng.

### Cách 2: Chạy bằng Bash Script [ralph_loop.sh](file:///home/avandall/project/Doulingo_Speak/Doulingo/ralph_loop.sh) trong Terminal Linux (Cần CLI + `tmux`/`nohup`)
Dành cho trường hợp chạy trên VPS hoặc không muốn mở giao diện IDE:
1. **Cài đặt AI CLI (Ví dụ Aider):**
   ```bash
   uv tool install --force --python 3.12 aider-chat
   ```
2. **Chạy qua đêm trong `tmux`:**
   ```bash
   # Cài tmux (trên Ubuntu/Debian)
   sudo apt-get install -y tmux

   # Tạo phiên làm việc và chạy script
   tmux new -s ralph
   chmod +x ralph_loop.sh
   ./ralph_loop.sh

   # Bấm Ctrl+B rồi bấm D để thoát tmux (script tiếp tục chạy qua đêm)
   ```

### 3. Cơ Chế Bảo Vệ 100% An Toàn Của Script
- **Tự động dừng khi hoàn tất:** Khi không còn checkbox `- [ ]` nào trong [specs.md](file:///home/avandall/project/Doulingo_Speak/Doulingo/docs/specs.md), script thông báo thành công và dừng.
- **Tự động phục hồi lỗi (Tip 18):** Sau mỗi lượt, script chạy `python -m py_compile main.py app/*.py`. Nếu xuất hiện lỗi cú pháp, script lập tức gọi `git reset --hard` để khôi phục commit ổn định gần nhất.
- **Lưu ký chi tiết (Overnight Logs):** Toàn bộ nhật ký từng lượt chạy được lưu tại `logs/ralph_loop_<timestamp>/iteration_<N>.log`.

---

## 💻 Chạy Ứng Dụng Cục Bộ (Local Development)

```bash
# Cài đặt phụ thuộc với uv
uv sync

# Khởi chạy server FastAPI
uv run uvicorn app.main:app --reload --port 8000
```
Truy cập ứng dụng tại: `http://localhost:8000`
