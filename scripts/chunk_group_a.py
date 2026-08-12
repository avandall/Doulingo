"""
chunk_group_a.py
=================
Bước 1 của pipeline (mục 3, 26_DB_solution.md): chia nhỏ 1 file .md thô của
Nhóm A ("Answer Bank") thành các chunk theo pattern "TOPIC N: TÊN" (hoặc biến
thể "Topic N.", "Chủ đề N:", v.v.), để mỗi chunk đưa cho LLM trích xuất riêng.

KHÔNG làm sạch nội dung ở bước này — chỉ cắt file thành các đoạn hợp lý theo
ranh giới topic. Việc lọc nhiễu vocab-column, tách câu hỏi/trả lời, gắn band
là việc của LLM ở bước 2 (extract_prompt_group_a.md).

Nếu file không có pattern "TOPIC N" nào (một số sách nhóm A dùng "Chủ đề N"
tiếng Việt, hoặc chỉ có heading tên chủ đề không đánh số), script sẽ tự thử
vài regex thay thế trước khi rơi về fallback: chunk cố định theo số từ, có
overlap nhẹ để không cắt đứt câu hỏi/trả lời ở ranh giới chunk.

Usage:
    python chunk_group_a.py <input.md> [--out-dir output/] [--max-words 1800]
"""

import argparse
import json
import re
from pathlib import Path

# Các pattern nhận diện ranh giới topic, thử theo thứ tự ưu tiên.
# Dùng re.MULTILINE + cho phép khoảng trắng đầu dòng (do PDF convert căn giữa).
TOPIC_PATTERNS = [
    # "TOPIC 5: CHOCOLATE" / "TOPIC 5. CHOCOLATE" / "Topic 5 - Chocolate"
    re.compile(r"^[ \t]*TOPIC\s+(\d+)[:.\-]?\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    # "Chủ đề 5: Sô cô la" / "CHỦ ĐỀ 5. ..."
    re.compile(r"^[ \t]*CH[ỦU]\s*ĐỀ\s+(\d+)[:.\-]?\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    # "Topic: Study" HOẶC "Topic T-shirts" (không đánh số, có/không có dấu ':')
    # — file Bai_mau_IELTS_Speaking_Part_1.md dùng lẫn cả 2 kiểu trong cùng 1 file,
    # nên bắt buộc phải chấp nhận dấu ':' là tuỳ chọn, không phải bắt buộc.
    re.compile(r"^[ \t]*Topic[:\s]+(.+)$", re.MULTILINE),
]


def find_topic_boundaries(text: str):
    """Thử từng pattern, trả về (pattern_used, list[Match]) cho pattern đầu tiên
    khớp được >= 2 lần (1 lần khớp không đủ để coi là cấu trúc lặp lại)."""
    for pat in TOPIC_PATTERNS:
        matches = list(pat.finditer(text))
        if len(matches) >= 2:
            return pat, matches
    return None, []


def chunk_by_topic(text: str, matches) -> list[dict]:
    chunks = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip("\n")
        groups = m.groups()
        topic_num = groups[0] if len(groups) > 1 and groups[0].isdigit() else None
        topic_name_guess = groups[-1].strip() if groups[-1] else None
        chunks.append(
            {
                "chunk_index": i,
                "topic_num_guess": topic_num,
                "topic_name_guess": topic_name_guess,
                "char_len": len(body),
                "word_len": len(body.split()),
                "text": body,
            }
        )
    return chunks


def chunk_fixed_size(text: str, max_words: int = 1800, overlap_words: int = 150) -> list[dict]:
    """Fallback khi không tìm được pattern topic lặp lại: cắt theo cụm ~max_words
    từ, có overlap để câu hỏi/trả lời không bị đứt giữa chừng ở ranh giới chunk.
    Cắt tại ranh giới dòng trống gần nhất với mốc max_words, không cắt giữa dòng.
    """
    lines = text.split("\n")
    chunks = []
    i = 0
    chunk_idx = 0
    while i < len(lines):
        word_count = 0
        j = i
        last_blank = None
        while j < len(lines) and word_count < max_words:
            word_count += len(lines[j].split())
            if lines[j].strip() == "":
                last_blank = j
            j += 1
        # Cắt tại dòng trống gần nhất nếu có, để không chẻ đôi 1 câu hỏi
        end = last_blank if (last_blank and last_blank > i) else j
        body = "\n".join(lines[i:end]).strip("\n")
        if body.strip():
            chunks.append(
                {
                    "chunk_index": chunk_idx,
                    "topic_num_guess": None,
                    "topic_name_guess": None,
                    "char_len": len(body),
                    "word_len": len(body.split()),
                    "text": body,
                }
            )
            chunk_idx += 1
        # Lùi lại overlap_words từ để chunk kế tiếp có ngữ cảnh gối đầu
        if end >= len(lines):
            break
        back = 0
        k = end
        while k > i and back < overlap_words:
            back += len(lines[k - 1].split())
            k -= 1
        i = max(k, i + 1)
    return chunks


def chunk_file(path: Path, max_words: int = 1800) -> dict:
    text = path.read_text(encoding="utf-8")
    pat, matches = find_topic_boundaries(text)
    if matches:
        chunks = chunk_by_topic(text, matches)
        method = "topic_pattern"
    else:
        chunks = chunk_fixed_size(text, max_words=max_words)
        method = "fixed_size_fallback"
    return {
        "source_file": path.name,
        "chunk_method": method,
        "num_chunks": len(chunks),
        "chunks": chunks,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="File .md thô cần chunk")
    ap.add_argument("--out-dir", type=Path, default=Path("output"))
    ap.add_argument("--max-words", type=int, default=1800)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    result = chunk_file(args.input, max_words=args.max_words)

    out_path = args.out_dir / f"{args.input.stem}.chunks.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[{result['chunk_method']}] {result['source_file']}: {result['num_chunks']} chunks")
    for c in result["chunks"][:5]:
        label = c["topic_name_guess"] or f"chunk {c['chunk_index']}"
        print(f"  - #{c['chunk_index']:>3}  {label!r:<40}  ~{c['word_len']} words")
    if result["num_chunks"] > 5:
        print(f"  ... ({result['num_chunks'] - 5} chunk khác, xem file JSON đầy đủ)")
    print(f"\nĐã ghi: {out_path}")


if __name__ == "__main__":
    main()