#!/usr/bin/env python3
# ==============================================================================
# 🔁 ralph_loop.py — Autonomous Build-Test-Fix Loop Runner (Antigravity Python SDK)
# ==============================================================================

import sys
import time
import subprocess
from pathlib import Path
from antigravity_sdk import AntigravitySDK

MAX_ITERATIONS = 10
TEST_COMMAND = "pytest"
SPECS_FILE = Path("docs/specs.md")
WORK_BOARD_FILE = Path("docs/WORK_BOARD.md")
BLOCKED_FILE = Path("docs/BLOCKED.md")


def check_remaining_tasks() -> bool:
    """Kiểm tra xem còn checkbox '[ ]' chưa hoàn thành trong docs/specs.md không."""
    if not SPECS_FILE.exists():
        print(f"❌ Không tìm thấy {SPECS_FILE}")
        return False
    content = SPECS_FILE.read_text(encoding="utf-8")
    return "[ ]" in content


def run_ralph_loop():
    print(f"🚀 [Ralph Loop - Python SDK] Khởi chạy vòng lặp tự động (Tối đa: {MAX_ITERATIONS} lần)...")
    
    # Khởi tạo Antigravity SDK với enable_subagents=True (*Tip 9*)
    agent = AntigravitySDK(
        enable_subagents=True,
        non_interactive=True,
        auto_approve=True,
    )

    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        print("=" * 72)
        print(f"🔄 [Ralph Loop - Python SDK] Lần lặp #{iteration} bắt đầu...")
        print("=" * 72)

        if not check_remaining_tasks():
            print("🎉 [Ralph Loop] Không còn mục '[ ]' nào trong docs/specs.md. Hoàn thành toàn bộ!")
            sys.exit(0)

        prompt_text = f"""
        Bạn đang chạy trong chế độ Autonomous Ralph Loop Mode (Tip 17, 28) với Python SDK.
        LƯU Ý: Bạn đã được bật enable_subagents=True, hãy sử dụng subagents để tìm kiếm codebase nếu cần (Tip 9).
        
        1. Đọc AGENTS.md và docs/rules.md để nắm quy chuẩn.
        2. Mở docs/specs.md, tìm ĐÚNG 1 mục checkbox chưa làm ('[ ]'), đổi trạng thái thành ('[/]') và cập nhật cột IN_PROGRESS trên docs/WORK_BOARD.md.
        3. Viết code triển khai đơn vị logic đó.
        4. Sau khi code xong, CHẠY LỆNH KIỂM THỬ: '{TEST_COMMAND}'.
        5. XỬ LÝ KẾT QUẢ:
           - Nếu test pass (Exit code 0):
             + Tạo git commit theo chuẩn Conventional Commits (Tip 10).
             + Đánh dấu '[x]' trong docs/specs.md và chuyển thành DONE trong docs/WORK_BOARD.md.
             + Thoát phiên với Exit code 0.
           - Nếu test fail (sau 2 lần tự sửa chữa):
             + Chạy lệnh 'git reset --hard HEAD' để xóa sạch code hỏng (Tip 18).
             + Ghi chi tiết lỗi vào docs/BLOCKED.md (Tip 16).
             + Thoát phiên với Exit code 2.
        """

        exit_code = agent.run(prompt=prompt_text)
        
        if exit_code == 0:
            print(f"✅ [Ralph Loop] Lần lặp #{iteration} thành công (Exit 0)! Chuyển sang mục tiếp theo...")
        elif exit_code == 2:
            print("🛑 [Ralph Loop] PHANH KHẨN CẤP (Exit 2)! Agent gặp cản trở. Xem ngay docs/BLOCKED.md.")
            sys.exit(2)
        else:
            print(f"⚠️ [Ralph Loop] Lần lặp #{iteration} gặp lỗi (Exit {exit_code}). Thử chạy lại...")
            
        time.sleep(2)

    print(f"🏁 [Ralph Loop] Đạt giới hạn tối đa ({MAX_ITERATIONS} lượt lặp).")


if __name__ == "__main__":
    run_ralph_loop()
