#!/usr/bin/env bash
# ==============================================================================
# 🔁 ralph_loop.sh — Autonomous Ralph Loop via Antigravity CLI ('agy')
# ==============================================================================
# Mỗi lượt lặp khởi chạy 1 phiên 'agy' mới (Fresh Context Window) để tránh tràn memory.
# Sử dụng tài khoản Antigravity Pro hiện tại của bạn.
# ==============================================================================

MAX_ITERATIONS=20
ITERATION=0
SPECS_FILE="docs/specs.md"
PROMPT_FILE="docs/prompt.md"

echo "🚀 [Ralph Loop - agy] Khởi chạy vòng lặp tự động với Antigravity CLI..."
echo "👤 Tài khoản: Google AI Pro (Gemini 3.6 Flash)"
echo ""

while [ $ITERATION -lt $MAX_ITERATIONS ]; do
  ITERATION=$((ITERATION + 1))
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  echo "========================================================================"
  echo "🔄 [$TIMESTAMP] Lần lặp #$ITERATION / $MAX_ITERATIONS — (Fresh Context Session)"
  echo "========================================================================"

  # BƯỚC 1: Kiểm tra xem còn task '[ ]' chưa làm không
  if ! grep -q "\[ \]" "$SPECS_FILE"; then
    echo "🎉 [Ralph Loop] Không còn mục '[ ]' nào trong $SPECS_FILE. Hoàn thành toàn bộ!"
    exit 0
  fi

  # BƯỚC 2: Gọi Antigravity CLI ('agy') ở chế độ non-interactive (Fresh Session)
  PROMPT_TEXT=$(cat "$PROMPT_FILE")
  
  agy --dangerously-skip-permissions -p "$PROMPT_TEXT"
  EXIT_CODE=$?

  # BƯỚC 3: Xử lý mã thoát
  if [ $EXIT_CODE -eq 2 ]; then
    echo "🛑 [Ralph Loop] PHANH KHẨN CẤP (Exit 2)! Xem chi tiết tại docs/BLOCKED.md."
    exit 2
  fi

  echo "⏳ Chờ 3 giây trước khi mở phiên làm việc mới (Next Task)..."
  sleep 3
done

echo "🏁 [Ralph Loop] Đạt giới hạn tối đa ($MAX_ITERATIONS lượt lặp)."
