"""
validate_yaml.py
================
Bước 3 pipeline (26_DB_solution.md mục 3): kiểm tra file YAML do LLM xuất ra
có đúng schema không TRƯỚC khi insert vào DB.

Chạy độc lập, không cần kết nối DB.

Usage:
    python validate_yaml.py <file.yaml>          # validate 1 file
    python validate_yaml.py output/extracted/    # validate cả thư mục

Exit code: 0 = tất cả pass, 1 = có file fail.
"""

import argparse
import sys
from pathlib import Path

import yaml

VALID_TEMPLATE_TYPES = {"band_ladder", "functional_bank", "scenario"}
VALID_REGISTERS      = {"casual", "neutral", "formal"}
VALID_TURN_TYPES     = {"standalone", "opening", "elaborate", "negotiation", "closing"}
BAND_MIN, BAND_MAX   = 1.0, 9.0
MIN_ANSWER_WORDS     = 5
MAX_ANSWER_WORDS     = 300


def err(path, msg):
    return {"file": path, "error": msg}

def check_band(val, field):
    if not isinstance(val, (int, float)):
        return f"{field} phải là số, nhận được: {type(val).__name__}"
    if not (BAND_MIN <= float(val) <= BAND_MAX):
        return f"{field}={val} ngoài khoảng [{BAND_MIN}, {BAND_MAX}]"
    if round(float(val) * 2) != float(val) * 2:
        return f"{field}={val} không phải bội của 0.5"
    return None

def word_count(text):
    return len(str(text).split())


def validate_doc(doc, filepath):
    errors = []

    cu = doc.get("content_unit")
    if not cu:
        errors.append(err(filepath, "Thiếu khối `content_unit`"))
        return errors

    for f in ("template_type", "title", "topic_tags",
              "target_band_min", "target_band_max", "register", "source_citation"):
        if f not in cu:
            errors.append(err(filepath, f"content_unit: thiếu field `{f}`"))

    if cu.get("template_type") not in VALID_TEMPLATE_TYPES:
        errors.append(err(filepath, f"content_unit.template_type không hợp lệ: {cu.get('template_type')!r}"))

    if cu.get("register") not in VALID_REGISTERS:
        errors.append(err(filepath, f"content_unit.register không hợp lệ: {cu.get('register')!r}"))

    for f in ("target_band_min", "target_band_max"):
        if f in cu:
            e = check_band(cu[f], f"content_unit.{f}")
            if e:
                errors.append(err(filepath, e))

    if ("target_band_min" in cu and "target_band_max" in cu
            and isinstance(cu["target_band_min"], (int, float))
            and isinstance(cu["target_band_max"], (int, float))
            and cu["target_band_min"] >= cu["target_band_max"]):
        errors.append(err(filepath, "target_band_min >= target_band_max"))

    tags = cu.get("topic_tags", [])
    if not isinstance(tags, list) or len(tags) == 0:
        errors.append(err(filepath, "content_unit.topic_tags phải là list không rỗng"))

    bt = doc.get("band_tiers", [])
    if not isinstance(bt, list) or len(bt) == 0:
        errors.append(err(filepath, "Thiếu hoặc rỗng `band_tiers`"))
    else:
        for i, t in enumerate(bt):
            prefix = f"band_tiers[{i}]"
            for f in ("band_min", "band_max"):
                if f not in t:
                    errors.append(err(filepath, f"{prefix}: thiếu field `{f}`"))
            for f in ("band_min", "band_max"):
                if f in t:
                    e = check_band(t[f], f"{prefix}.{f}")
                    if e:
                        errors.append(err(filepath, e))
            for f in ("grammar_required", "vocabulary_core"):
                if not isinstance(t.get(f), list):
                    errors.append(err(filepath, f"{prefix}.{f} phải là list"))

    sds = doc.get("sample_dialogues", [])
    if not isinstance(sds, list) or len(sds) == 0:
        errors.append(err(filepath, "Thiếu hoặc rỗng `sample_dialogues`"))
    else:
        for i, sd in enumerate(sds):
            prefix = f"sample_dialogues[{i}]"
            for f in ("band_level", "turn_type", "ai_line", "user_model_answer"):
                if f not in sd:
                    errors.append(err(filepath, f"{prefix}: thiếu field `{f}`"))

            if "band_level" in sd:
                e = check_band(sd["band_level"], f"{prefix}.band_level")
                if e:
                    errors.append(err(filepath, e))

            if sd.get("turn_type") not in VALID_TURN_TYPES:
                errors.append(err(filepath, f"{prefix}.turn_type không hợp lệ: {sd.get('turn_type')!r}"))

            answer = str(sd.get("user_model_answer", "")).strip()
            wc = word_count(answer)
            if wc < MIN_ANSWER_WORDS:
                errors.append(err(filepath, f"{prefix}.user_model_answer quá ngắn ({wc} từ): {answer!r}"))
            if wc > MAX_ANSWER_WORDS:
                errors.append(err(filepath, f"{prefix}.user_model_answer quá dài ({wc} từ)"))

            # Phát hiện nhiễu vocab-column còn sót
            for sig in [" (n)=", " (v)=", " (adj)=", "(n): "]:
                if sig in answer:
                    errors.append(err(filepath, f"{prefix}: còn nhiễu vocab-column ({sig!r})"))
                    break

    return errors


def validate_file(path):
    text = path.read_text(encoding="utf-8")
    try:
        docs = [d for d in yaml.safe_load_all(text) if d is not None]
    except yaml.YAMLError as e:
        return 0, 1, [err(str(path), f"YAML parse error: {e}")]

    if not docs:
        return 0, 1, [err(str(path), "File YAML rỗng")]

    passed = failed = 0
    all_errors = []
    for i, doc in enumerate(docs):
        if isinstance(doc, str) and doc.strip() == "SKIP":
            continue
        if not isinstance(doc, dict):
            failed += 1
            all_errors.append(err(f"{path.name}[doc {i}]", f"Unsupported YAML document type: {type(doc).__name__}"))
            continue
        doc_errors = validate_doc(doc, f"{path.name}[doc {i}]")
        if doc_errors:
            failed += 1
            all_errors.extend(doc_errors)
        else:
            passed += 1
    return passed, failed, all_errors


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    files = sorted(args.input.glob("*.yaml")) + sorted(args.input.glob("*.yml")) \
        if args.input.is_dir() else [args.input]

    if not files:
        print("Không tìm thấy file YAML nào.")
        sys.exit(1)

    total_pass = total_fail = 0
    all_errors = []
    for f in files:
        p, fail, errs = validate_file(f)
        total_pass += p
        total_fail += fail
        all_errors.extend(errs)

    if not args.quiet:
        for e in all_errors:
            print(f"  ✗ [{e['file']}] {e['error']}")

    print(f"\n{'='*60}")
    print(f"Kết quả: {total_pass} PASS | {total_fail} FAIL | {len(all_errors)} lỗi")
    print("Sẵn sàng insert DB" if total_fail == 0 else "Cần sửa trước khi insert")
    print('='*60)
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
