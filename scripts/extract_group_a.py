import argparse
import json
import re
from pathlib import Path

import yaml

VIETNAMESE_QUESTION_PREFIXES = [
    "Bạn", "Có", "Không", "Tại sao", "Bạn có", "Bạn đã", "Bạn nghĩ", "Bạn thường", "Bạn làm", "Bạn đang", "Bạn sẽ"  # common starts
]


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_") or "unknown"


def is_vietnamese_question_line(line: str) -> bool:
    if not line:
        return False
    for prefix in VIETNAMESE_QUESTION_PREFIXES:
        if line.startswith(prefix):
            return True
    # Vietnamese often contains diacritics; if the line has many, treat it as Vietnamese.
    if len(re.findall(r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]", line.lower())) >= 2:
        return True
    return False


MIN_ANSWER_WORDS = 5
MAX_ANSWER_WORDS = 300


def clean_answer_lines(lines: list[str]) -> str:
    text = " ".join(line.strip() for line in lines if line.strip())
    text = remove_vocab_noise(text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    return text.strip()


PAGE_BREAK_MARKERS = ("---",)


def is_footer_line(stripped: str) -> bool:
    """Dòng footer lặp lại mỗi trang PDF (vd 'Kho tài liệu tự học IELTS ... Khoá học
    IELTS Online') hoặc dấu phân trang '---'. Những dòng này cần được BỎ QUA (skip)
    khi đang thu thập câu trả lời, KHÔNG được coi là ranh giới dừng — vì đôi khi
    page-break rơi ngay giữa 1 câu trả lời đang viết dở (vd Q6 topic Study)."""
    if not stripped:
        return False
    if stripped in PAGE_BREAK_MARKERS:
        return True
    if "Kho tài liệu" in stripped or stripped.startswith("Source:"):
        return True
    return False


def is_section_boundary_line(stripped: str) -> bool:
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    if stripped.startswith("---"):
        return True
    boundary_phrases = [
        "Frequently-Asked Questions",
        "Useful Words and Expressions",
        "Important Chinese Traditional Festivals",
        "Dialogue Study",
        "Practice Questions",
        "Table completion",
        "Matching",
        "Personal answer",
        "Correction:",
        "Answer:",
        "Yes/No/Maybe",
        "What happened...",
        "Vocabulary",
        "Pronunciation",
        "Grammar",
        "Useful words",
        "Tips",
        "Key words",
    ]
    lower = stripped.lower()
    for phrase in boundary_phrases:
        if phrase.lower() in lower:
            return True
    return False


def is_placeholder_answer(answer: str) -> bool:
    stripped = answer.strip()
    if not stripped:
        return True
    if len(stripped.split()) < 5:
        return True
    placeholders = [
        "*answer:",
        "*correction:",
        "answer: ____________________________________________",
        "correction: ____________________________________________",
        "__",
        "personal answer",
        "similar to above",
        "same as above",
        "table completion",
        "matching",
        "reason:",
        "consequence:",
    ]
    lower = stripped.lower()
    for p in placeholders:
        if p in lower:
            return True
    return False


def remove_vocab_noise(text: str) -> str:
    # Loại bỏ annotation kiểu "(n): ..." hoặc "(v)=..." hay các kí hiệu tương tự
    text = re.sub(r"\s*\([^\)]*\)\s*[:=]\s*[^\n\r]*(?=\s|$)", "", text)
    text = re.sub(r"\s*\b(n|v|adj)\b\s*=\s*[^\n\r]*(?=\s|$)", "", text)
    return text


def find_question_start_lines(lines: list[str]) -> list[tuple[int, str]]:
    """Trả về vị trí các dòng bắt đầu 1 câu hỏi (dạng 'N. ...'), KHÔNG yêu cầu
    dấu '?' ngay trên chính dòng này — vì câu hỏi có thể trải nhiều dòng và có
    thể kết thúc bằng hậu tố dạng '(Why?)' thay vì dấu '?' ở cuối cùng."""
    start_re = re.compile(r"^(\d+)\.\s+\S")
    starts = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if start_re.match(stripped):
            starts.append((i, stripped))
    return starts


def parse_chunk_text(text: str) -> list[dict]:
    lines = text.splitlines()
    starts = find_question_start_lines(lines)
    if not starts:
        return []

    questions = []
    for idx, (qpos, _first_line) in enumerate(starts):
        next_start = starts[idx + 1][0] if idx + 1 < len(starts) else len(lines)

        # --- Bước 1: gom dòng câu hỏi, có thể trải nhiều dòng, dừng ngay khi
        # gặp dấu '?' (kể cả khi '?' nằm giữa dòng, trước 1 hậu tố ngoặc đơn
        # như '(Why?)') — tối đa 5 dòng lookahead để tránh gom nhầm cả câu trả
        # lời nếu vì lý do gì đó không có dấu '?' (dữ liệu lỗi).
        q_lines = []
        j = qpos
        found_qmark = False
        while j < next_start and (j - qpos) < 5:
            raw_stripped = lines[j].strip()
            if raw_stripped:
                q_lines.append(raw_stripped)
            if "?" in raw_stripped:
                found_qmark = True
                j += 1
                break
            j += 1
        if not found_qmark:
            # Không tìm thấy dấu '?' trong 5 dòng — không đoán mò, bỏ qua theo
            # đúng nguyên tắc "không bịa/không giữ dữ liệu không chắc chắn".
            continue
        qtext = re.sub(r"\s+", " ", " ".join(q_lines)).strip()

        # --- Bước 2: gom câu trả lời từ sau câu hỏi tới trước câu hỏi kế tiếp.
        # Footer/page-break bị BỎ QUA (không dừng thu thập) để không cắt cụt
        # câu trả lời nếu page-break rơi giữa chừng.
        answer_lines: list[str] = []
        m = j
        while m < next_start:
            raw = lines[m]
            stripped = raw.strip()
            if is_footer_line(stripped):
                m += 1
                continue
            if is_section_boundary_line(stripped) and answer_lines:
                break
            if is_vietnamese_question_line(stripped) and answer_lines:
                break
            answer_lines.append(raw)
            m += 1
        answer = clean_answer_lines(answer_lines)
        wc = len(answer.split())
        if not answer or is_placeholder_answer(answer) or wc < MIN_ANSWER_WORDS or wc > MAX_ANSWER_WORDS:
            continue
        questions.append({"ai_line": qtext, "user_model_answer": answer})
    return questions


def is_boilerplate(text: str) -> bool:
    """Detect obvious non-content chunks (TOC, footers, ads, contact info).
    Return True when chunk should be SKIPped according to pipeline rules.
    """
    if not text or len(text.strip()) < 40:
        return True
    low = text.lower()
    patterns = [
        "mục lục",
        "table of contents",
        "table contents",
        "kho tài liệu",
        "khoá học",
        "click",
        "tải",
        "download",
        "email",
        "tuvan@",
        "contact",
        "source:",
        "©",
        "đăng ký",
        "bảng theo dõi",
        "feedback",
        "phone",
        "website",
    ]
    for p in patterns:
        if p in low:
            return True
    # If the text is mostly keywords list or headings (many short lines), skip
    lines = [line_str for line_str in text.splitlines() if line_str.strip()]
    short_lines = sum(1 for line_str in lines if len(line_str.strip()) < 60)
    if len(lines) >= 5 and short_lines / len(lines) > 0.6:
        return True
    return False


def build_content_unit(file_name: str, topic: str, topic_slug: str) -> dict:
    title = f"{topic} — Answer Bank"
    return {
        "content_unit": {
            "template_type": "band_ladder",
            "title": title,
            "topic_tags": [topic_slug],
            "target_band_min": 6.5,
            "target_band_max": 8.5,
            "register": "neutral",
            "source_citation": f"{file_name}, Topic: {topic}",
        },
        "band_tiers": [
            {
                "band_min": 6.5,
                "band_max": 8.5,
                "can_do_description": f"Trả lời các câu hỏi Part 1 về {topic.lower()} bằng các câu ghép, có lý do và ví dụ cụ thể.",
                "grammar_required": ["present simple", "comparative", "linking with and/but"],
                "vocabulary_core": [topic_slug.replace("_", " ")],
                "vocabulary_stretch": [],
                "sentence_length_target": "2-3 câu/câu trả lời, có mệnh đề phụ",
            }
        ],
    }


def dump_yaml(data: dict, out_path: Path) -> None:
    with out_path.open("w", encoding="utf-8") as f:
        yaml.dump(data, f, sort_keys=False, allow_unicode=True, width=1000)


def extract_all(chunks_dir: Path, out_dir: Path) -> list[tuple[str, int, int]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = []
    for chunk_file in sorted(chunks_dir.glob("*.chunks.json")):
        raw = json.loads(chunk_file.read_text(encoding="utf-8"))
        source_file = raw.get("source_file", chunk_file.stem)
        for chunk in raw.get("chunks", []):
            idx = chunk.get("chunk_index")
            topic_guess = chunk.get("topic_name_guess") or "unknown"
            topic_line = None
            if not topic_guess:
                for line in chunk.get("text", "").splitlines():
                    match = re.match(r"^\s*(?:Topic|TOPIC|Chủ đề|CHỦ ĐỀ)[:\.]?\s*(.+)$", line, re.IGNORECASE)
                    if match:
                        topic_line = match.group(1).strip()
                        break
                if topic_line:
                    topic_guess = topic_line
            topic = topic_guess.strip() or "Unknown"
            topic_slug = slugify(topic)
            text = chunk.get("text", "")

            # THỨ TỰ QUAN TRỌNG: parse trước, chỉ dùng is_boilerplate() làm lý do
            # SKIP khi parse không ra được sample_dialogue nào.
            # (Bug cũ: is_boilerplate() bị gọi TRƯỚC parse, và vì nó chỉ tìm keyword
            # kiểu "kho tài liệu"/"download"/"email" xuất hiện ở BẤT KỲ ĐÂU trong
            # chunk, một chunk 2000+ từ đầy đủ Q&A thật vẫn bị SKIP oan chỉ vì có
            # dính 1 dòng footer lặp lại mỗi trang PDF. Parse trước đảm bảo nội
            # dung thật luôn được ưu tiên giữ lại, boilerplate-check chỉ còn vai
            # trò phân biệt "chunk trống vì đúng là rác" và "chunk trống vì lỗi
            # parse" khi ghi log.)
            if len(text.strip()) < 40:
                out_path = out_dir / f"{chunk_file.stem}_chunk_{idx}.yaml"
                out_path.write_text("SKIP\n", encoding="utf-8")
                summary.append((chunk_file.name, idx, 0))
                continue

            sample_dialogues = parse_chunk_text(text)
            if not sample_dialogues:
                # Không trích được cặp Q&A nào — SKIP, dù lý do là boilerplate
                # thật (mục lục, quảng cáo) hay chỉ đơn giản là chunk này không
                # có câu hỏi đánh số nào (vd trang bìa, lời giới thiệu).
                out_path = out_dir / f"{chunk_file.stem}_chunk_{idx}.yaml"
                out_path.write_text("SKIP\n", encoding="utf-8")
                summary.append((chunk_file.name, idx, 0))
                continue

            yaml_obj = build_content_unit(source_file, topic, topic_slug)
            yaml_obj["sample_dialogues"] = []
            for item in sample_dialogues:
                band_level = 7.5 if len(item["user_model_answer"]) > 120 else 7.0
                yaml_obj["sample_dialogues"].append(
                    {
                        "band_level": band_level,
                        "turn_type": "standalone",
                        "ai_line": item["ai_line"],
                        "user_model_answer": item["user_model_answer"],
                    }
                )
            out_name = f"{chunk_file.stem}_chunk_{idx}.yaml"
            out_path = out_dir / out_name
            dump_yaml(yaml_obj, out_path)
            summary.append((chunk_file.name, idx, len(sample_dialogues)))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract chunk JSON files into YAML sample dialogues.")
    parser.add_argument("chunks_dir", type=Path, help="Directory containing .chunks.json files")
    parser.add_argument("out_dir", type=Path, help="Output directory for extracted YAML files")
    args = parser.parse_args()
    summary = extract_all(args.chunks_dir, args.out_dir)
    print(f"Extracted {len(summary)} chunk YAML files to {args.out_dir}")
    for src, idx, count in summary[:20]:
        print(f"{src}  chunk {idx}: {count} sample_dialogues")
    if len(summary) > 20:
        print(f"... and {len(summary)-20} more")


if __name__ == "__main__":
    main()