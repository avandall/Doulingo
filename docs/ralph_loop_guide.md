# 🦉 Hướng Dẫn Chạy Tự Động "Ralph Loop" Qua Đêm Thành Công 100% (Harness Engineering Guide)

Tài liệu này hướng dẫn chi tiết cách vận hành luồng phát triển phần mềm tự động bằng AI (**Ralph Loop**) cho dự án **Duolingo Speak Clone**, được đúc kết từ video [Harness Engineering: 29 Tips to Build the Systems That Build Software](https://www.youtube.com/watch?v=rraHPF4ZgCw).

---

## 1. Triết Lý "Ralph Loop" & Harness Engineering

Trong "Harness Engineering", thay vì kỹ sư ngồi can thiệp thủ công sửa từng lỗi trong chat với AI, ta xây dựng một **bộ dây cương (Harness)** gồm tài liệu chuẩn, luật lệ chặt chẽ và kịch bản tự động hóa để AI tự lặp lại chu trình **Build - Test - Fix - Commit**.

### 4 Trường Cột Triết Lý:
1. **"One Item, One Fresh Chat" (Tip 15):** Mỗi lần chạy chỉ nhận 01 task từ `docs/specs.md`. Phiên chạy hoàn toàn mới (fresh context), ngăn chặn suy thoái bộ nhớ (context rot).
2. **"Don't Describe Code, Point To It" (Tip 4 & 5):** Tài liệu (`docs/architecture.md`) trỏ trực tiếp đến code thực tế, giúp AI tuân thủ DNA kiến trúc hiện có.
3. **"Never Compact Your Chat" (Tip 8):** Không tóm tắt hay nén chat history. Thông tin được ghi nhớ qua hệ thống file documentation trong repo.
4. **"Recover with Git Reset" (Tip 18):** Nếu AI code hỏng làm lỗi cú pháp hoặc thất bại khi kiểm thử, hệ thống tự động gọi `git reset --hard` khôi phục commit ổn định gần nhất trước khi thử lại.

---

## 2. Hệ Thống Tài Liệu Harness Của Dự Án

| File | Vai trò trong Ralph Loop |
| :--- | :--- |
| **`docs/architecture.md`** | Sơ đồ kiến trúc, cấu trúc thư mục, luồng hội thoại dài, Duolingo Design Tokens. |
| **`docs/rules.md`** | Các quy tắc coding (Python 3.12+, UV, Duolingo UI `#58CC02`, fallback AI) & kiểm thử bắt buộc. |
| **`docs/specs.md`** | Danh sách backlog dưới dạng checkbox (`- [ ]`). Agent đọc và đổi thành `- [x]` sau khi xong. |
| **`docs/prompt.md`** | System prompt đưa vào CLI Agent mỗi lượt lặp (yêu cầu đọc doc -> chọn 1 task -> code -> test -> commit -> exit). |
| **`ralph_loop.sh`** | Script điều phối chính (Bảo vệ qua đêm, quản lý git reset, lưu log, kiểm tra điều kiện kết thúc). |

---

## 3. Hướng Dẫn Thực Hành: 2 Cách Chạy Qua Đêm (Antigravity IDE vs Terminal CLI)

Tùy thuộc vào thói quen và môi trường làm việc, bạn có **2 cách** để vận hành Ralph Loop qua đêm:

---

### Cách 1: Chạy Trực Tiếp Trong Antigravity IDE Với `/goal` (⭐ Khuyên Dùng - KHÔNG CẦN Cài CLI, KHÔNG CẦN Cài `tmux`)

Khi bạn đang sử dụng **Antigravity IDE**, bản thân IDE chính là một AI Agent mạnh mẽ được tích hợp sẵn hệ thống thực thi tự động.

* **Có cần cài thêm CLI (`aider`, `claude`) không?** ➔ **KHÔNG CẦN.** Bạn dùng chính model hiện tại của IDE (Gemini 3.1 Pro / Claude 3.7 Sonnet).
* **Có cần cài `tmux` không?** ➔ **KHÔNG CẦN.** IDE tự động duy trì phiên làm việc trong nền của ứng dụng.

#### Các bước thực hiện chạy qua đêm với Antigravity IDE:
1. **Chuẩn bị nguồn điện & chế độ ngủ của máy tính:**
   - Cắm sạc máy tính.
   - Vào cài đặt hệ điều hành (Linux/macOS/Windows), chuyển chế độ **Sleep / Suspend** khi cắm nguồn sang **Never** (Không bao giờ ngủ) để máy chạy thâu đêm.
2. **Kích hoạt lệnh `/goal` trong khung chat Antigravity IDE:**
   - Nhập lệnh `/goal` vào thanh chat kèm prompt sau:
     ```
     /goal Hãy thực hiện toàn bộ các nhiệm vụ chưa hoàn thành (- [ ]) trong docs/specs.md theo triết lý Ralph Loop: đọc docs -> chọn 1 task -> code -> test cú pháp -> cập nhật [x] -> commit. Không dừng lại cho đến khi hoàn thành 100% tất cả checkbox trong docs/specs.md!
     ```
3. **Để máy tự chạy qua đêm:**
   - Antigravity IDE sẽ tự động đọc backlog từ `docs/specs.md`, tuần tự viết code, chạy kiểm tra cú pháp, đánh dấu hoàn thành và tiếp tục task tiếp theo cho đến sáng hôm sau.

---

### Cách 2: Chạy Bằng Bash Script `ralph_loop.sh` Trong Terminal (Dành cho chạy ngoài IDE hoặc trên Server Linux)

Nếu bạn muốn chạy script bash độc lập ngoài trình duyệt/IDE (ví dụ qua SSH trên VPS Linux):

* **Có cần cài CLI không?** ➔ **CÓ.** Script `ralph_loop.sh` là một shell script gọi lệnh từ command line, nên bạn cần cài 1 AI CLI trong terminal Linux, ví dụ:
  - Cài **Aider** (phổ biến nhất cho Ralph Loop):
    ```bash
    uv tool install --force --python 3.12 aider-chat
    # hoặc: pipx install aider-chat
    ```
  - Cài **Claude Code CLI**:
    ```bash
    npm install -g @anthropic-ai/claude-code
    ```
* **Có cần cài `tmux` không?** ➔ **KHÔNG BẮT BUỘC nhưng KHUYÊN DÙNG.**
  - **Cách 2A (Dùng `tmux` - Khuyên dùng):** `tmux` giúp bạn đóng terminal mà script vẫn chạy ngầm.
    ```bash
    # Cài tmux (trên Ubuntu/Debian)
    sudo apt-get install -y tmux

    # Tạo phiên làm việc mới
    tmux new -s ralph

    # Chạy script
    ./ralph_loop.sh

    # Bấm Ctrl+B rồi bấm D để thoát tmux (script tiếp tục chạy qua đêm)
    ```
  - **Cách 2B (Không cần `tmux` - Dùng `nohup`):**
    ```bash
    chmod +x ralph_loop.sh
    nohup ./ralph_loop.sh > overnight_ralph.log 2>&1 &
    ```
    Script sẽ chạy dưới nền hệ điều hành và ghi toàn bộ log vào `overnight_ralph.log`.

---

### 3.1 Thiết Lập Biến Môi Trường Cho Script `ralph_loop.sh` (Nếu dùng Cách 2)

Mặc định, script sử dụng lệnh:
```bash
aider --message-file docs/prompt.md --yes
```

Bạn có thể thay đổi công cụ AI bằng cách gán biến `AGENT_CMD`:

- **Dùng với Claude Code CLI:**
  ```bash
  export AGENT_CMD="claude -p 'Read docs/prompt.md and execute it'"
  ```
- **Dùng với Gemini CLI / Custom Python Agent:**
  ```bash
  export AGENT_CMD="gemini --prompt-file docs/prompt.md"
  ```
- **Dùng với Aider (Khuyên dùng cho autonomous coding):**
  ```bash
  export AGENT_CMD="aider --message-file docs/prompt.md --yes"
  ```

### 3.2 Cách Chạy Qua Đêm (Overnight Execution)

Để script không bị dừng khi bạn tắt máy tính hoặc mất kết nối SSH, hãy chạy trong `tmux`, `screen` hoặc `nohup`:

#### Cách A: Chạy trong `tmux` (Khuyên dùng)
```bash
# 1. Tạo phiên tmux mới
tmux new -s ralph

# 2. Cấp quyền thực thi cho script (nếu chưa có)
chmod +x ralph_loop.sh

# 3. Bắt đầu chạy Ralph Loop
./ralph_loop.sh

# 4. Bấm Ctrl+b rồi bấm d để thoát khỏi tmux (script vẫn chạy qua đêm bên trong)
```

#### Cách B: Chạy dưới nền với `nohup`
```bash
chmod +x ralph_loop.sh
nohup ./ralph_loop.sh > ralph_overnight.log 2>&1 &
```

---

## 4. Cơ Chế Bảo Vệ & Phục Hồi Tự Động (Why It's 100% Reliable)

1. **Tự động kiểm tra hoàn tất (Loop Termination):**
   - Trước mỗi lượt chạy, script kiểm tra file `docs/specs.md`. Nếu không còn mục `- [ ]` nào, script hiển thị thông báo chiến thắng và dừng lại an toàn.
2. **Kiểm tra cú pháp sau lặp (Syntax Guard):**
   - Sau khi Agent hoàn tất, script thực thi:
     ```bash
     python -m py_compile main.py app/*.py
     ```
   - Nếu phát hiện lỗi cú pháp Python, script lập tức **cảnh báo** và thực thi:
     ```bash
     git reset --hard $LAST_GOOD_COMMIT
     git clean -fd
     ```
   - Repo luôn được hoàn tác về trạng thái ổn định, ngăn không cho code lỗi tích tụ qua đêm.
3. **Giám sát nhật ký chi tiết (Overnight Logs):**
   - Toàn bộ output của mỗi lượt chạy được lưu tại thư mục `logs/ralph_loop_<timestamp>/iteration_<N>.log`. Sáng hôm sau bạn có thể kiểm tra chính xác Agent đã làm gì trong từng bước.
4. **Giới hạn số lượt tối đa (Max Iterations Guard):**
   - Mặc định script giới hạn `MAX_ITERATIONS=30` (có thể chỉnh qua `export MAX_ITERATIONS=50`). Tránh lặp vô hạn nếu gặp task không thể giải quyết.
