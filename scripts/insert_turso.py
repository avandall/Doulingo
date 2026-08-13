"""
insert_turso.py
===============
Bước 4 pipeline: parse YAML đã validate → INSERT vào Turso DB.

QUAN TRỌNG — cách dùng:
  Bước 1 (local test): chạy với --dry-run để xem SQL sẽ chạy, không động DB.
  Bước 2 (local test): chạy với --sqlite để test logic insert vào SQLite local.
  Bước 3 (production): chạy thật với --turso-url + --turso-token.

Usage:
    # Xem SQL sẽ chạy (không insert gì cả)
    python insert_turso.py output/extracted/ --dry-run

    # Test với SQLite local (tạo file test.db)
    python insert_turso.py output/extracted/ --sqlite test.db

    # Insert thật vào Turso
    python insert_turso.py output/extracted/ \
        --turso-url libsql://your-db.turso.io \
        --turso-token your_token_here

Embedding:
    Script này KHÔNG tự gọi embedding API (để bạn chọn model tuỳ thích:
    OpenAI text-embedding-3-small 1536d, hoặc sentence-transformers 384d).
    Cột embedding được insert NULL và cập nhật riêng bằng script
    generate_embeddings.py (xem file đó).
"""

import argparse
import json
import sqlite3
import sys
import uuid
from pathlib import Path

import yaml

# ─── DDL Turso (libSQL) — dùng cú pháp SQLite tương thích ──────────────────
# Turso dùng libSQL là superset của SQLite, nên DDL này chạy được cả 2 nơi.
# Điểm khác với Postgres: không có UUID type, dùng TEXT; không có ARRAY,
# dùng JSON string; vector dùng F32_BLOB(384) — nhưng ở đây ta tạm NULL.

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS content_units (
    id              TEXT PRIMARY KEY,
    template_type   TEXT NOT NULL CHECK(template_type IN ('band_ladder','functional_bank','scenario')),
    title           TEXT NOT NULL,
    topic_tags      TEXT NOT NULL DEFAULT '[]',   -- JSON array string: '["chocolate","food"]'
    target_band_min REAL,
    target_band_max REAL,
    register        TEXT,
    source_citation TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now')),
    version         INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS band_tiers (
    id                    TEXT PRIMARY KEY,
    content_unit_id       TEXT NOT NULL REFERENCES content_units(id) ON DELETE CASCADE,
    band_min              REAL NOT NULL,
    band_max              REAL NOT NULL,
    can_do_description    TEXT,
    grammar_required      TEXT DEFAULT '[]',   -- JSON array string
    vocabulary_core       TEXT DEFAULT '[]',   -- JSON array string
    vocabulary_stretch    TEXT DEFAULT '[]',   -- JSON array string
    vocabulary_avoid      TEXT DEFAULT '[]',   -- JSON array string
    sentence_length_target TEXT,
    common_errors_to_simulate TEXT
);
CREATE INDEX IF NOT EXISTS idx_band_tiers_range ON band_tiers (band_min, band_max);

CREATE TABLE IF NOT EXISTS sample_dialogues (
    id              TEXT PRIMARY KEY,
    content_unit_id TEXT NOT NULL REFERENCES content_units(id) ON DELETE CASCADE,
    band_level      REAL NOT NULL,
    turn_type       TEXT,
    function_tag    TEXT,
    ai_line         TEXT NOT NULL,
    user_model_answer TEXT NOT NULL,
    embedding       BLOB,   -- NULL until generate_embeddings.py chạy
    created_at      TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sd_band ON sample_dialogues (band_level);
CREATE INDEX IF NOT EXISTS idx_sd_cu   ON sample_dialogues (content_unit_id);

CREATE TABLE IF NOT EXISTS hook_bank (
    id          TEXT PRIMARY KEY,
    topic_tags  TEXT DEFAULT '[]',   -- JSON array, NULL = dùng chung mọi topic
    text        TEXT NOT NULL,
    type        TEXT CHECK(type IN ('hook','anti_cliche'))
);

CREATE TABLE IF NOT EXISTS vocabulary_lookup (
    id       TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    tier     TEXT,
    terms    TEXT DEFAULT '[]'   -- JSON array
);

CREATE TABLE IF NOT EXISTS user_profile (
    user_id               TEXT PRIMARY KEY,
    band_estimate_overall REAL,
    band_fluency          REAL,
    band_lexical          REAL,
    band_grammar          REAL,
    band_pronunciation    REAL,
    recurring_errors      TEXT DEFAULT '[]',
    updated_at            TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS user_content_exposure (
    id                 TEXT PRIMARY KEY,
    user_id            TEXT REFERENCES user_profile(user_id),
    sample_dialogue_id TEXT REFERENCES sample_dialogues(id),
    exposed_at         TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_exposure_user_time ON user_content_exposure (user_id, exposed_at);
"""

# ─── Helper ─────────────────────────────────────────────────────────────────

def new_id() -> str:
    return str(uuid.uuid4())

def to_json(val) -> str:
    if isinstance(val, list):
        return json.dumps(val, ensure_ascii=False)
    if val is None:
        return "[]"
    return json.dumps([val], ensure_ascii=False)

def get_conn_sqlite(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def get_conn_turso(url: str, token: str):
    """
    Kết nối Turso thật qua libsql-client.
    Package: pip install libsql-client
    Nếu chưa install: script thoát với hướng dẫn.
    """
    try:
        import libsql_client  # type: ignore
    except ImportError:
        print("Chưa install libsql-client. Chạy: pip install libsql-client")
        sys.exit(1)
    return libsql_client.create_client_sync(url=url, auth_token=token)

# ─── Insert functions ────────────────────────────────────────────────────────

def insert_doc(doc: dict, conn, dry_run: bool, source_file: str) -> dict:
    """Insert 1 YAML document. Trả về stats."""
    stats = {"content_units": 0, "band_tiers": 0, "sample_dialogues": 0, "skipped": 0}
    cu_data = doc["content_unit"]

    cu_id = new_id()

    # ── content_units ──────────────────────────────────────────────────────
    cu_sql = """
    INSERT OR IGNORE INTO content_units
        (id, template_type, title, topic_tags, target_band_min, target_band_max,
         register, source_citation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    cu_params = (
        cu_id,
        cu_data["template_type"],
        cu_data["title"],
        to_json(cu_data.get("topic_tags", [])),
        cu_data.get("target_band_min"),
        cu_data.get("target_band_max"),
        cu_data.get("register"),
        cu_data.get("source_citation", source_file),
    )

    if dry_run:
        print("\n[DRY RUN] content_units INSERT:")
        print(f"  id={cu_id[:8]}... title={cu_data['title']!r}")
    else:
        conn.execute(cu_sql, cu_params)
    stats["content_units"] += 1

    # ── band_tiers ─────────────────────────────────────────────────────────
    tier_sql = """
    INSERT OR IGNORE INTO band_tiers
        (id, content_unit_id, band_min, band_max, can_do_description,
         grammar_required, vocabulary_core, vocabulary_stretch,
         sentence_length_target)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for tier in doc.get("band_tiers", []):
        tier_params = (
            new_id(), cu_id,
            tier["band_min"], tier["band_max"],
            tier.get("can_do_description"),
            to_json(tier.get("grammar_required", [])),
            to_json(tier.get("vocabulary_core", [])),
            to_json(tier.get("vocabulary_stretch", [])),
            tier.get("sentence_length_target"),
        )
        if dry_run:
            print(f"  [DRY RUN] band_tiers INSERT: band {tier['band_min']}-{tier['band_max']}")
        else:
            conn.execute(tier_sql, tier_params)
        stats["band_tiers"] += 1

    # ── sample_dialogues ───────────────────────────────────────────────────
    sd_sql = """
    INSERT OR IGNORE INTO sample_dialogues
        (id, content_unit_id, band_level, turn_type, function_tag,
         ai_line, user_model_answer, embedding)
    VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
    """
    for sd in doc.get("sample_dialogues", []):
        sd_params = (
            new_id(), cu_id,
            sd["band_level"],
            sd.get("turn_type", "standalone"),
            sd.get("function_tag"),
            sd["ai_line"],
            sd["user_model_answer"],
        )
        if dry_run:
            print(f"  [DRY RUN] sample_dialogues INSERT: band={sd['band_level']} "
                  f"q={sd['ai_line'][:50]!r}")
        else:
            conn.execute(sd_sql, sd_params)
        stats["sample_dialogues"] += 1

    # ── hook_bank ──────────────────────────────────────────────────────────
    hook_sql = """
    INSERT OR IGNORE INTO hook_bank
        (id, topic_tags, text, type)
    VALUES (?, ?, ?, ?)
    """
    for hook in doc.get("hook_bank", []):
        hook_params = (
            new_id(),
            to_json(hook.get("topic_tags", [])),
            hook["text"],
            hook.get("type", "hook"),
        )
        if dry_run:
            print(f"  [DRY RUN] hook_bank INSERT: type={hook.get('type')} text={hook['text'][:30]!r}")
        else:
            conn.execute(hook_sql, hook_params)
        stats.setdefault("hook_bank", 0)
        stats["hook_bank"] += 1

    # ── vocabulary_lookup ──────────────────────────────────────────────────
    vocab_sql = """
    INSERT OR IGNORE INTO vocabulary_lookup
        (id, category, tier, terms)
    VALUES (?, ?, ?, ?)
    """
    for vocab in doc.get("vocabulary_lookup", []):
        vocab_params = (
            new_id(),
            vocab["category"],
            vocab.get("tier"),
            to_json(vocab.get("terms", [])),
        )
        if dry_run:
            print(f"  [DRY RUN] vocabulary_lookup INSERT: category={vocab['category']!r}")
        else:
            conn.execute(vocab_sql, vocab_params)
        stats.setdefault("vocabulary_lookup", 0)
        stats["vocabulary_lookup"] += 1

    return stats



def process_file(path: Path, conn, dry_run: bool, is_turso: bool):
    text = path.read_text(encoding="utf-8")
    docs = [d for d in yaml.safe_load_all(text) if d is not None]

    total = {"content_units": 0, "band_tiers": 0, "sample_dialogues": 0}
    for doc in docs:
        stats = insert_doc(doc, conn, dry_run, path.name)
        for k in total:
            total[k] += stats[k]

    if not dry_run and not is_turso:
        conn.commit()

    return total, len(docs)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="File .yaml hoặc thư mục chứa .yaml")
    ap.add_argument("--dry-run", action="store_true",
                    help="In SQL sẽ chạy, không insert thật")
    ap.add_argument("--sqlite", type=str, metavar="DB_PATH",
                    help="Insert vào SQLite local thay vì Turso (để test)")
    ap.add_argument("--turso-url", type=str)
    ap.add_argument("--turso-token", type=str)
    args = ap.parse_args()

    # Kiểm tra mode
    if not args.dry_run and not args.sqlite and not args.turso_url:
        print("Cần chọn 1 trong 3 mode: --dry-run | --sqlite <path> | --turso-url + --turso-token")
        sys.exit(1)

    # Lấy danh sách file
    if args.input.is_dir():
        files = sorted(args.input.glob("*.yaml")) + sorted(args.input.glob("*.yml"))
    else:
        files = [args.input]

    if not files:
        print("Không tìm thấy file YAML.")
        sys.exit(1)

    # Setup DB connection
    is_turso = False
    conn = None

    if args.dry_run:
        print(f"[DRY RUN MODE] Sẽ xử lý {len(files)} file, không insert thật.\n")
        # Dùng SQLite in-memory để test schema DDL
        conn = sqlite3.connect(":memory:")
        conn.executescript(SCHEMA_SQL)
    elif args.sqlite:
        print(f"[SQLITE MODE] DB: {args.sqlite}")
        conn = get_conn_sqlite(args.sqlite)
        conn.executescript(SCHEMA_SQL)
        print("Schema khởi tạo xong.\n")
    elif args.turso_url:
        if not args.turso_token:
            print("--turso-token bắt buộc khi dùng --turso-url")
            sys.exit(1)
        is_turso = True
        conn = get_conn_turso(args.turso_url, args.turso_token)
        # Turso: chạy schema qua execute batch
        for stmt in SCHEMA_SQL.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(stmt)
                except Exception:
                    pass  # Bảng đã tồn tại → ignore
        print(f"[TURSO MODE] Đã kết nối: {args.turso_url}\n")

    # Process
    grand_total = {"content_units": 0, "band_tiers": 0, "sample_dialogues": 0}
    for f in files:
        try:
            total, n_docs = process_file(f, conn, args.dry_run, is_turso)
            print(f"✓ {f.name}: {n_docs} doc → "
                  f"{total['content_units']} content_units, "
                  f"{total['band_tiers']} band_tiers, "
                  f"{total['sample_dialogues']} sample_dialogues")
            for k in grand_total:
                grand_total[k] += total[k]
        except Exception as e:
            print(f"✗ {f.name}: LỖI — {e}")

    print(f"\n{'='*60}")
    print(f"TỔNG: {grand_total['content_units']} content_units | "
          f"{grand_total['band_tiers']} band_tiers | "
          f"{grand_total['sample_dialogues']} sample_dialogues")
    if args.dry_run:
        print("(Dry run — không có gì được insert thật)")
    elif args.sqlite:
        print(f"Đã ghi vào: {args.sqlite}")
    else:
        print("Đã insert vào Turso.")
    print('='*60)

    if conn and not is_turso:
        conn.close()


if __name__ == "__main__":
    main()
