"""
fix_yaml_lists.py
=================
Auto-fix các lỗi YAML list phổ biến do LLM sinh ra trước khi validate.

Chạy TRƯỚC validate_yaml.py:
    python fix_yaml_lists.py output/extracted/      # fix cả thư mục
    python fix_yaml_lists.py file.yaml              # fix 1 file

Các lỗi được fix tự động:
  1. Flow sequence [...] chứa dấu phẩy trong ngoặc đơn '' hoặc ngoặc tròn ()
     → chuyển thành block sequence (dạng - item)
  2. Dấu phẩy kép ,, trong list
  3. Markdown code fence ```yaml ... ``` bọc ngoài YAML
  4. Item rỗng trong list (do ,, hoặc [, item])

File gốc được backup thành *.bak trước khi sửa.
"""

import argparse
import re
import shutil
from pathlib import Path


# ── Các regex phát hiện vấn đề ───────────────────────────────────────────────

# Dòng có flow sequence [...] chứa nội dung có khả năng xung đột với YAML parser:
# - dấu nháy đơn ' bên trong
# - ngoặc tròn () bên trong
# - dấu phẩy kép ,,
SUSPECT_FLOW_RE = re.compile(
    r"^(\s*\w[\w_ ]*:\s*)\[(.+)\]\s*$"
)

# Dấu phẩy kép
DOUBLE_COMMA_RE = re.compile(r",\s*,")

# Markdown fence
MD_FENCE_RE = re.compile(r"^```(?:yaml)?\s*\n?", re.MULTILINE)
MD_FENCE_END_RE = re.compile(r"\n?```\s*$", re.MULTILINE)


def has_complex_content(items_str: str) -> bool:
    """Kiểm tra list có chứa nội dung phức tạp cần chuyển sang block sequence."""
    # Nháy đơn bên trong
    if "'" in items_str:
        return True
    # Ngoặc tròn bên trong (ví dụ: "e.g., ..." hoặc "(complex)")
    if "(" in items_str:
        return True
    return False


def flow_to_block(indent: str, key_part: str, items_str: str) -> str:
    """Chuyển `key: [a, b, c]` thành block sequence.

    key_part: phần "  grammar_required: "
    items_str: phần bên trong [...] chưa được parse
    """
    # Parse thủ công: tách item bằng dấu phẩy, nhưng bỏ qua dấu phẩy
    # bên trong ngoặc tròn () hoặc nháy đơn ''
    items = _split_flow_items(items_str)
    items = [i.strip().strip("\"'") for i in items if i.strip()]

    if not items:
        return f"{key_part}[]\n"

    # Tái tạo block sequence
    # key_part có thể là "  grammar_required: " → lấy indent từ đó
    lines = [f"{key_part}\n"]
    # Tính indent cho các item (2 space thêm vào so với key)
    item_indent = " " * (len(key_part) - len(key_part.lstrip()) + 2)
    for item in items:
        # Nếu item có ký tự đặc biệt YAML, bọc trong double-quote
        if any(c in item for c in ["'", ":", "#", "[", "]", "{", "}"]):
            item = '"' + item.replace('"', '\\"') + '"'
        lines.append(f"{item_indent}- {item}\n")
    return "".join(lines)


def _split_flow_items(s: str) -> list[str]:
    """Tách các item trong flow sequence, bỏ qua dấu phẩy bên trong () và ''."""
    items = []
    current = []
    depth_paren = 0
    in_quote = False
    quote_char = None

    i = 0
    while i < len(s):
        c = s[i]

        if in_quote:
            current.append(c)
            if c == quote_char:
                in_quote = False
                quote_char = None
        elif c in ("'", '"'):
            in_quote = True
            quote_char = c
            current.append(c)
        elif c == "(":
            depth_paren += 1
            current.append(c)
        elif c == ")":
            depth_paren -= 1
            current.append(c)
        elif c == "," and depth_paren == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(c)
        i += 1

    if current:
        items.append("".join(current).strip())

    return [it for it in items if it]


def fix_content(text: str) -> tuple[str, int]:
    """Fix YAML text. Trả về (fixed_text, n_fixes)."""
    fixes = 0

    # Fix 1: bỏ markdown fence
    if MD_FENCE_RE.search(text) or MD_FENCE_END_RE.search(text):
        text = MD_FENCE_RE.sub("", text)
        text = MD_FENCE_END_RE.sub("", text)
        text = text.strip() + "\n"
        fixes += 1

    # Fix 2: dấu phẩy kép
    if DOUBLE_COMMA_RE.search(text):
        text = DOUBLE_COMMA_RE.sub(",", text)
        fixes += 1

    # Fix 4: register — chuẩn hoá giá trị LLM hay tự bịa về đúng enum
    REGISTER_MAP = {
        "academic": "formal",
        "semi-formal": "formal",
        "conversational": "casual",
        "informal": "casual",
        "professional": "formal",
    }
    for wrong, right in REGISTER_MAP.items():
        pattern = f"register: {wrong}"
        if pattern in text:
            text = text.replace(pattern, f"register: {right}")
            fixes += 1

    # Fix 3: flow sequence phức tạp → block sequence
    lines = text.split("\n")
    new_lines = []
    for line in lines:
        m = SUSPECT_FLOW_RE.match(line)
        if m:
            key_part = m.group(1)   # vd "  grammar_required: "
            items_str = m.group(2)  # vd "Past simple, 'used to' for past"
            if has_complex_content(items_str):
                # Chuyển sang block sequence
                fixed = flow_to_block("", key_part, items_str)
                new_lines.append(fixed.rstrip("\n"))
                fixes += 1
                continue
        new_lines.append(line)
    text = "\n".join(new_lines)

    # Đảm bảo kết thúc bằng newline
    if not text.endswith("\n"):
        text += "\n"

    return text, fixes


def fix_file(path: Path, backup: bool = True) -> int:
    """Fix 1 file. Trả về số fix đã thực hiện."""
    original = path.read_text(encoding="utf-8")
    fixed, n_fixes = fix_content(original)

    if n_fixes > 0:
        if backup:
            shutil.copy2(path, path.with_suffix(".yaml.bak"))
        path.write_text(fixed, encoding="utf-8")

    return n_fixes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path,
                    help="File .yaml hoặc thư mục chứa .yaml")
    ap.add_argument("--no-backup", action="store_true",
                    help="Không tạo file .bak")
    args = ap.parse_args()

    files = (sorted(args.input.glob("**/*.yaml"))
             if args.input.is_dir() else [args.input])
    # Bỏ qua file backup
    files = [f for f in files if not f.name.endswith(".bak")]

    if not files:
        print("Không tìm thấy file YAML.")
        return

    total_fixed = 0
    total_files = 0
    for f in files:
        try:
            n = fix_file(f, backup=not args.no_backup)
            if n > 0:
                print(f"  ✓ {f.name}: {n} fix")
                total_files += 1
                total_fixed += n
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")

    print(f"\n{'='*50}")
    print(f"Fix xong: {total_files} file | {total_fixed} chỗ sửa")
    if total_files > 0:
        print(f"Chạy validate tiếp: python scripts/validate_yaml.py {args.input}")
    print("="*50)


if __name__ == "__main__":
    main()
