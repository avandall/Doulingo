#!/usr/bin/env python3
"""
Tool khắc phục & đồng bộ thứ tự lịch sử chat cho Antigravity IDE.

Chức năng:
1. Quét toàn bộ cơ sở dữ liệu hội thoại trong ~/.gemini/antigravity-ide/conversations & brain/
2. Checkpoint SQLite WAL journal dở dang sau khi IDE bị crash
3. Cập nhật mtime (last modified) của file .db và folder brain theo đúng thời gian tin nhắn mới nhất
4. Liệt kê danh sách hội thoại chuẩn xác 100% theo thứ tự mới nhất -> cũ nhất
5. Xuất nội dung phiên chat gần nhất hoặc bất kỳ phiên nào ra Markdown khi UI không hiển thị
"""

import os
import sys
import glob
import json
import time
import sqlite3
import argparse
from datetime import datetime

GEMINI_DIR = os.path.expanduser("~/.gemini/antigravity-ide")
CONV_DIR = os.path.join(GEMINI_DIR, "conversations")
BRAIN_DIR = os.path.join(GEMINI_DIR, "brain")

def checkpoint_sqlite_wal(db_path: str):
    """Thực hiện checkpoint SQLite WAL để gom dữ liệu chưa flush sau crash."""
    if not os.path.exists(db_path):
        return
    wal_path = f"{db_path}-wal"
    if os.path.exists(wal_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()
        except Exception:
            pass

def get_latest_timestamp_from_transcript(conv_id: str) -> tuple[float, str, str]:
    """
    Đọc transcript.jsonl để lấy:
    - Timestamp tin nhắn cuối cùng (float epoch)
    - Câu hỏi đầu tiên (tiêu đề phiên)
    - Câu hỏi cuối cùng
    """
    transcript_file = os.path.join(BRAIN_DIR, conv_id, ".system_generated", "logs", "transcript.jsonl")
    first_query = "(Không có tin nhắn)"
    last_query = "(Không có tin nhắn)"
    latest_ts = 0.0

    if os.path.exists(transcript_file):
        try:
            latest_ts = os.path.getmtime(transcript_file)
            with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
                user_msgs = []
                for line in f:
                    if '"type":"USER_INPUT"' in line:
                        d = json.loads(line)
                        content = d.get("content", "").replace("<USER_REQUEST>", "").strip()
                        first_line = content.split("\n")[0].strip()
                        if first_line:
                            user_msgs.append(first_line)
                        created_at = d.get("created_at")
                        if created_at:
                            try:
                                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                                msg_epoch = dt.timestamp()
                                if msg_epoch > latest_ts:
                                    latest_ts = msg_epoch
                            except Exception:
                                pass
                if user_msgs:
                    first_query = user_msgs[0][:90]
                    last_query = user_msgs[-1][:90]
        except Exception:
            pass
    else:
        # Fallback to .db mtime
        db_path = os.path.join(CONV_DIR, f"{conv_id}.db")
        if os.path.exists(db_path):
            latest_ts = os.path.getmtime(db_path)

    return latest_ts, first_query, last_query

def scan_all_conversations():
    """Quét và gom thông tin toàn bộ các phiên chat."""
    conv_ids = set()
    if os.path.exists(CONV_DIR):
        for f in os.listdir(CONV_DIR):
            if f.endswith(".db"):
                conv_ids.add(f[:-3])
    if os.path.exists(BRAIN_DIR):
        for d in os.listdir(BRAIN_DIR):
            if os.path.isdir(os.path.join(BRAIN_DIR, d)) and d != "tempmediaStorage":
                conv_ids.add(d)

    items = []
    for cid in conv_ids:
        db_file = os.path.join(CONV_DIR, f"{cid}.db")
        checkpoint_sqlite_wal(db_file)
        latest_ts, first_q, last_q = get_latest_timestamp_from_transcript(cid)
        items.append({
            "id": cid,
            "timestamp": latest_ts,
            "time_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest_ts)) if latest_ts > 0 else "N/A",
            "title": first_q,
            "last_msg": last_q,
            "has_db": os.path.exists(db_file),
            "has_brain": os.path.exists(os.path.join(BRAIN_DIR, cid)),
        })

    items.sort(key=lambda x: x["timestamp"], reverse=True)
    return items

def sync_timestamps(items):
    """
    Sửa mtime trên filesystem của các file .db và thư mục brain
    để ép hệ thống file và bất kỳ tiến trình quét nào cũng thấy đúng thứ tự mới nhất.
    """
    count = 0
    now = time.time()
    for item in items:
        ts = item["timestamp"]
        if ts <= 0:
            continue
        cid = item["id"]
        db_file = os.path.join(CONV_DIR, f"{cid}.db")
        brain_folder = os.path.join(BRAIN_DIR, cid)
        
        try:
            if os.path.exists(db_file):
                os.utime(db_file, (ts, ts))
            if os.path.exists(brain_folder):
                os.utime(brain_folder, (ts, ts))
            count += 1
        except Exception:
            pass
    print(f"✅ Đã đồng bộ timestamp (mtime) cho {count} phiên hội thoại thành công!")

def export_conversation(conv_id: str, out_file: str | None = None):
    """Trích xuất toàn bộ nội dung chat ra định dạng Markdown."""
    transcript_file = os.path.join(BRAIN_DIR, conv_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.exists(transcript_file):
        print(f"❌ Không tìm thấy transcript cho phiên ID: {conv_id}")
        return

    turns = []
    with open(transcript_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            step_type = d.get("type")
            source = d.get("source")
            content = d.get("content", "")
            if step_type == "USER_INPUT" and source == "USER_EXPLICIT":
                turns.append(("user", d.get("created_at", ""), content))
            elif step_type == "PLANNER_RESPONSE" and source == "MODEL" and content:
                turns.append(("assistant", d.get("created_at", ""), content))

    md_lines = [f"# Lịch Sử Hội Thoại (Session ID: {conv_id})\n"]
    for role, ts, text in turns:
        if role == "user":
            md_lines.append(f"### 👤 Người Dùng ({ts})\n")
            md_lines.append(f"{text.strip()}\n")
        else:
            md_lines.append(f"### 🤖 Trợ Lý AI ({ts})\n")
            md_lines.append(f"{text.strip()}\n")
        md_lines.append("\n---\n")

    result = "\n".join(md_lines)
    if out_file:
        out_dir = os.path.dirname(out_file)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"✅ Đã xuất đoạn chat ra file: {out_file}")
    else:
        print(result)

def main():
    parser = argparse.ArgumentParser(description="Khắc phục & sắp xếp lịch sử chat Antigravity IDE")
    parser.add_argument("--list", "-l", action="store_true", help="Liệt kê danh sách hội thoại theo thứ tự mới nhất")
    parser.add_argument("--limit", type=int, default=15, help="Số lượng hội thoại hiển thị (mặc định 15)")
    parser.add_argument("--sync", "-s", action="store_true", help="Đồng bộ mtime và flush WAL checkpoint")
    parser.add_argument("--export", "-e", type=str, help="Xuất nội dung chat theo Session ID (hoặc 'latest')")
    parser.add_argument("--out", "-o", type=str, help="Đường dẫn file markdown xuất ra")

    args = parser.parse_args()

    items = scan_all_conversations()

    if args.sync or (not args.list and not args.export):
        sync_timestamps(items)

    if args.list or (not args.export):
        print(f"\n📋 DANH SÁCH {min(args.limit, len(items))} PHIÊN CHAT GẦN NHẤT (ĐÃ SORT MỚI NHẤT -> CŨ NHẤT):\n")
        print(f"{'STT':<4} {'Thời gian':<20} {'Session ID':<38} {'Tiêu đề / Tin nhắn đầu tiên'}")
        print("-" * 110)
        for idx, it in enumerate(items[:args.limit]):
            print(f"{idx+1:<4} {it['time_str']:<20} {it['id']:<38} {it['title']}")
        print("-" * 110)
        print("💡 Gợi ý: Chạy với `--export latest --out chat_gannhat.md` để lưu đoạn chat gần nhất ra file.")

    if args.export:
        target_id = args.export
        if target_id == "latest":
            if items:
                # Lấy phiên ngay trước phiên hiện tại nếu phiên hiện tại là phiên đang chạy
                curr_cid = os.environ.get("CONVERSATION_ID", "")
                target_id = items[0]["id"]
                if target_id == curr_cid and len(items) > 1:
                    target_id = items[1]["id"]
            else:
                print("❌ Không có phiên chat nào.")
                return
        print(f"Đang xuất phiên: {target_id}...")
        export_conversation(target_id, args.out)

if __name__ == "__main__":
    main()
