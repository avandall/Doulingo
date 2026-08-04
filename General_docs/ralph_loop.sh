#!/usr/bin/env bash
# ==============================================================================
# 🔁 ralph_loop.sh — Autonomous Build-Test-Fix Loop Runner (Antigravity CLI/IDE)
# ==============================================================================
#
# 🛠️ CÁCH SETUP CHẾ ĐỘ NON-INTERACTIVE VỚI ANTIGRAVITY CLI / IDE:
# 1. Cấu hình quyền (Permissions):
#    Trong Antigravity config hoặc cờ thực thi CLI, bật chế độ tự động phê duyệt
#    (auto-approve) cho các thao tác:
#    - write_file (chỉnh sửa file trong codebase)
#    - run_command (chạy test, git status, git commit)
# 2. Bật Subagent (Tip 9 - Spawn Helper Agents):
#    - Nếu gọi qua Python SDK: bật tham số `enable_subagents=True`.
#    - Nếu gọi qua CLI: thêm cờ `--enable-subagents` vào câu lệnh bên dưới.
# 3. Câu lệnh gọi Antigravity ở chế độ tự động hóa:
#    Sử dụng lệnh: `antigravity --non-interactive --enable-subagents --prompt "..."`
# 4. Yêu cầu kiểm thử:
#    Đảm bảo biến `TEST_COMMAND` bên dưới được gán đúng lệnh chạy test của dự án
#    (ví dụ: pytest, npm test, cargo test, v.v.).
# a. nohup uv run ralph_loop.sh  > ralph.log 2>&1 &
# b. Mở tmux, chạy uv run python ralph_loop.py  -> Nhấn Ctrl + b rồi buông tay ra nhấn phím d (Detach) để thoát ra ngoài cho máy tự chạy.
# ==============================================================================

MAX_ITERATIONS=10 # Số phiên AI tối đa chạy tự động trong 1 đêm
ITERATION=0
TEST_COMMAND="pytest" # <- Thay bằng lệnh kiểm thử tự động của dự án bạn

echo "🚀 [Ralph Loop - Antigravity] Khởi chạy vòng lặp tự động (Tối đa: $MAX_ITERATIONS lần)..."

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  ITERATION=$((ITERATION + 1))
  echo "========================================================================"
  echo "🔄 [Ralph Loop - Antigravity] Lần lặp #$ITERATION bắt đầu..."
  echo "========================================================================"

  # BƯỚC 1: Kiểm tra xem trong docs/specs.md còn checkbox '[ ]' nào chưa làm không
  if ! grep -q "\[ \]" docs/specs.md; then
    echo "🎉 [Ralph Loop] Không còn mục '[ ]' nào trong docs/specs.md. Hoàn thành toàn bộ!"
    exit 0
  fi

  # BƯỚC 2: Gọi Antigravity CLI ở chế độ Non-Interactive cho đúng 1 Spec Item (Tip 15)
  echo "🤖 [Ralph Loop] Đang gọi Antigravity agent để xử lý 1 mục từ docs/specs.md..."

  antigravity --non-interactive --prompt "
    Bạn đang chạy trong chế độ Autonomous Ralph Loop Mode (Tip 17, 28).
    1. Đọc AGENTS.md và docs/rules.md để nắm quy chuẩn.
    2. Mở docs/specs.md, tìm ĐÚNG 1 mục checkbox chưa làm ('[ ]'), đổi trạng thái thành ('[/]') và cập nhật cột IN_PROGRESS trên docs/WORK_BOARD.md.
    3. Viết code triển khai đơn vị logic đó.
    4. Sau khi code xong, CHẠY LỆNH KIỂM THỬ: '$TEST_COMMAND'.
    5. XỬ LÝ KẾT QUẢ:
       - Nếu test pass (Exit code 0):
         + Tạo git commit theo chuẩn Conventional Commits (Tip 10).
         + Đánh dấu '[x]' trong docs/specs.md và chuyển thành DONE trong docs/WORK_BOARD.md.
         + Thoát phiên với Exit code 0.
       - Nếu test fail (sau 2 lần tự sửa chữa):
         + Chạy lệnh 'git reset --hard HEAD' để xóa sạch code hỏng (Tip 18).
         + Ghi chi tiết lỗi vào docs/BLOCKED.md (Tip 16).
         + Thoát phiên với Exit code 2.
  "

  # BƯỚC 3: Nhận Mã thoát (Exit Code) từ Antigravity session vừa xong
  EXIT_CODE=$?

  # BƯỚC 4: Điều hướng vòng lặp theo Exit Code
  if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ [Ralph Loop] Lần lặp #$ITERATION thành công (Exit 0)! Chuyển sang mục tiếp theo..."
  elif [ $EXIT_CODE -eq 2 ]; then
    echo "🛑 [Ralph Loop] PHANH KHẨN CẤP (Exit 2)! Agent gặp cản trở. Xem ngay docs/BLOCKED.md."
    exit 2 # Dừng hẳn script để kỹ sư con người can thiệp
  else
    echo "⚠️ [Ralph Loop] Lần lặp #$ITERATION gặp lỗi chưa xác định (Exit $EXIT_CODE). Thử chạy lại..."
  fi

  sleep 2
done

echo "🏁 [Ralph Loop] Đạt giới hạn tối đa ($MAX_ITERATIONS lượt lặp)."
