"""
generate_embeddings.py
======================
Chạy SAU insert_turso.py — cập nhật cột `embedding` cho các row
sample_dialogues còn NULL.

Hỗ trợ 2 embedding backend:
  A) OpenAI text-embedding-3-small (1536 chiều) — chất lượng cao hơn
  B) sentence-transformers all-MiniLM-L6-v2 (384 chiều) — chạy local, miễn phí

Turso dùng F32_BLOB(N) — script tự serialize list[float] → bytes theo
little-endian float32, đúng định dạng Turso native vector.

Usage:
    # Dùng OpenAI (cần OPENAI_API_KEY trong env)
    python generate_embeddings.py --sqlite test.db --backend openai

    # Dùng sentence-transformers local (cần: pip install sentence-transformers)
    python generate_embeddings.py --sqlite test.db --backend local

    # Turso thật
    python generate_embeddings.py \
        --turso-url libsql://your-db.turso.io \
        --turso-token your_token \
        --backend openai

    # Chỉ xử lý N row đầu (để test)
    python generate_embeddings.py --sqlite test.db --backend local --limit 10

KHUYẾN NGHỊ cho production:
    Dùng backend `local` (all-MiniLM-L6-v2, 384 chiều) trong giai đoạn đầu:
    - Miễn phí, không giới hạn số lượt gọi
    - 384 chiều đủ tốt cho retrieval theo topic/band (không phải semantic search phức tạp)
    - Khi có budget, migrate sang openai 1536 chiều sau và reindex
    Schema Turso: F32_BLOB(384) cho local, F32_BLOB(1536) cho openai
"""

import argparse
import os
import sqlite3
import struct
import sys
import time

# ─── Embedding backends ──────────────────────────────────────────────────────

def embed_openai(texts: list[str], model="text-embedding-3-small") -> list[list[float]]:
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        print("Chưa install openai. Chạy: pip install openai")
        sys.exit(1)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Thiếu OPENAI_API_KEY trong environment.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    resp = client.embeddings.create(model=model, input=texts)
    return [item.embedding for item in resp.data]


_LOCAL_MODEL = None


def embed_local(texts: list[str], model_name="all-MiniLM-L6-v2") -> list[list[float]]:
    global _LOCAL_MODEL
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ImportError:
        print("Chưa install sentence-transformers. Chạy: pip install sentence-transformers")
        sys.exit(1)

    if _LOCAL_MODEL is None:
        _LOCAL_MODEL = SentenceTransformer(model_name, device="cpu")
    vecs = _LOCAL_MODEL.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vecs]


# ─── Serialization: list[float] → bytes (F32_BLOB Turso format) ─────────────

def floats_to_blob(vec: list[float]) -> bytes:
    """Little-endian float32 array — đúng định dạng F32_BLOB của libSQL/Turso."""
    return struct.pack(f"<{len(vec)}f", *vec)


# ─── Text để embed ───────────────────────────────────────────────────────────

def build_embed_text(row: dict) -> str:
    """
    Ghép ai_line + user_model_answer + topic (nếu có) thành 1 chuỗi để embed.
    Cùng công thức này phải dùng ở retrieval layer khi tạo query vector.
    """
    parts = []
    if row.get("topic_tags"):
        parts.append(f"topic: {row['topic_tags']}")
    if row.get("ai_line"):
        parts.append(f"Q: {row['ai_line']}")
    if row.get("user_model_answer"):
        parts.append(f"A: {row['user_model_answer']}")
    return " | ".join(parts)


# ─── DB adapters ─────────────────────────────────────────────────────────────

class SqliteAdapter:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

    def fetch_null_embeddings(self, limit: int | None) -> list[dict]:
        sql = """
            SELECT sd.id, sd.ai_line, sd.user_model_answer,
                   cu.topic_tags
            FROM sample_dialogues sd
            JOIN content_units cu ON sd.content_unit_id = cu.id
            WHERE sd.embedding IS NULL
        """
        if limit:
            sql += f" LIMIT {limit}"
        return [dict(r) for r in self.conn.execute(sql).fetchall()]

    def update_embedding(self, row_id: str, blob: bytes):
        self.conn.execute(
            "UPDATE sample_dialogues SET embedding = ? WHERE id = ?",
            (blob, row_id)
        )

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class TursoAdapter:
    """Adapter cho libsql-client khi chạy production."""
    def __init__(self, url: str, token: str):
        try:
            import libsql_client  # type: ignore
        except ImportError:
            print("Chưa install libsql-client. Chạy: pip install libsql-client")
            sys.exit(1)
        self.client = libsql_client.create_client_sync(url=url, auth_token=token)

    def fetch_null_embeddings(self, limit):
        sql = """
            SELECT sd.id, sd.ai_line, sd.user_model_answer, cu.topic_tags
            FROM sample_dialogues sd
            JOIN content_units cu ON sd.content_unit_id = cu.id
            WHERE sd.embedding IS NULL
        """
        if limit:
            sql += f" LIMIT {limit}"
        result = self.client.execute(sql)
        return [dict(zip(result.columns, row)) for row in result.rows]

    def update_embedding(self, row_id: str, blob: bytes):
        self.client.execute(
            "UPDATE sample_dialogues SET embedding = ? WHERE id = ?",
            [blob, row_id]
        )

    def commit(self):
        pass  # libsql-client tự commit mỗi execute

    def close(self):
        self.client.close()


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=["openai", "local"], required=True)
    ap.add_argument("--sqlite", type=str, metavar="DB_PATH")
    ap.add_argument("--turso-url", type=str)
    ap.add_argument("--turso-token", type=str)
    ap.add_argument("--batch-size", type=int, default=32,
                    help="Số row embed mỗi batch API call (default 32)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Chỉ xử lý N row đầu (để test)")
    args = ap.parse_args()

    # Setup DB
    if args.sqlite:
        db = SqliteAdapter(args.sqlite)
        print(f"[SQLITE] {args.sqlite}")
    elif args.turso_url:
        db = TursoAdapter(args.turso_url, args.turso_token or "")
        print(f"[TURSO] {args.turso_url}")
    else:
        print("Cần --sqlite hoặc --turso-url")
        sys.exit(1)

    # Lấy danh sách row cần embed
    rows = db.fetch_null_embeddings(args.limit)
    if not rows:
        print("Không có row nào cần embed (embedding đã đầy đủ).")
        return

    print(f"Cần embed: {len(rows)} rows | backend: {args.backend} | batch: {args.batch_size}")

    embed_fn = embed_openai if args.backend == "openai" else embed_local

    # Xử lý theo batch
    processed = 0
    for i in range(0, len(rows), args.batch_size):
        batch = rows[i:i + args.batch_size]
        texts = [build_embed_text(r) for r in batch]

        try:
            vecs = embed_fn(texts)
        except Exception as e:
            print(f"  ✗ Batch {i//args.batch_size + 1} FAILED: {e}")
            continue

        for row, vec in zip(batch, vecs):
            blob = floats_to_blob(vec)
            db.update_embedding(row["id"], blob)
            processed += 1

        db.commit()
        print(f"  ✓ Batch {i//args.batch_size + 1}: {len(batch)} rows embedded "
              f"({processed}/{len(rows)} tổng)")

        # Rate limit cho OpenAI (tránh 429)
        if args.backend == "openai" and i + args.batch_size < len(rows):
            time.sleep(0.5)

    db.close()
    print(f"\n{'='*60}")
    print(f"Hoàn thành: {processed}/{len(rows)} rows đã có embedding")
    print('='*60)


if __name__ == "__main__":
    main()
