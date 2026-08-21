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

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── Multi-Key Pool Manager ──────────────────────────────────────────────────

class GeminiKeyPool:
    def __init__(self):
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
        except ImportError:
            pass
        raw = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_KEY") or ""
        self.keys = [k.strip() for k in raw.split(",") if k.strip()]
        self.current_idx = 0
        if not self.keys:
            print("Thiếu GEMINI_API_KEY, GOOGLE_API_KEY hoặc GEMINI_KEY trong .env / environment.")
            sys.exit(1)

    def get_current_key(self) -> str:
        return self.keys[self.current_idx]

    def rotate(self) -> str:
        if len(self.keys) <= 1:
            return self.get_current_key()
        self.current_idx = (self.current_idx + 1) % len(self.keys)
        new_key_masked = self.keys[self.current_idx][:8] + "..." + self.keys[self.current_idx][-4:]
        print(f"  ➜ [API Key Switch] Đổi sang Key #{self.current_idx + 1}/{len(self.keys)} ({new_key_masked})")
        return self.keys[self.current_idx]


# ─── Embedding backends ──────────────────────────────────────────────────────

def embed_gemini(texts: list[str], key_pool: GeminiKeyPool, model: str = "gemini-embedding-2") -> list[list[float]]:
    """
    Embedding dùng Google AI Studio Gemini API (`gemini-embedding-2`, 3072 dimensions).
    Hỗ trợ xoay vòng nhiều API Key (dấu phẩy trong .env) & tự động retry khi đụng Rate Limit (429).
    """
    model_path = model if model.startswith("models/") else f"models/{model}"
    import requests

    max_retries = max(len(key_pool.keys) * 3, 6)
    retry_delay = 2.0

    for attempt in range(max_retries):
        api_key = key_pool.get_current_key()
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:batchEmbedContents?key={api_key}"
        payload = {
            "requests": [
                {
                    "model": model_path,
                    "content": {"parts": [{"text": t}]}
                }
                for t in texts
            ]
        }
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("embeddings", []):
                    if "values" in item:
                        results.append(item["values"])
                    elif isinstance(item, dict) and "embedding" in item and "values" in item["embedding"]:
                        results.append(item["embedding"]["values"])
                if len(results) == len(texts):
                    return results
                print(f"  ⚠️ Cảnh báo: trả về {len(results)}/{len(texts)} vectors. Retry...")

            # Nếu đụng Rate Limit (429) hoặc Quota limit (403/429)
            if resp.status_code in (429, 403, 500, 503):
                err_msg = resp.json().get("error", {}).get("message", resp.text[:100])
                print(f"  ⚠️ Gemini API Limit (Status {resp.status_code}): {err_msg[:80]}")
                if len(key_pool.keys) > 1:
                    key_pool.rotate()
                print(f"  ⏳ Chờ {retry_delay:.1f}s để hồi phục RPM/TPM limit (Lần thử {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 30.0)
            else:
                raise RuntimeError(f"Gemini API Error {resp.status_code}: {resp.text}")

        except requests.RequestException as e:
            print(f"  ⚠️ Kết nối lỗi: {e}. Retry ({attempt + 1}/{max_retries})...")
            time.sleep(retry_delay)
            retry_delay = min(retry_delay * 1.5, 10.0)

    raise RuntimeError(f"Thất bại sau {max_retries} lần thử do đụng API Rate Limit liên tục.")


def embed_openai(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return embed_local(texts)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"input": texts, "model": model}
    res = requests.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload, timeout=30)
    if res.status_code != 200:
        return embed_local(texts)
    data = res.json()
    return [item["embedding"] for item in data.get("data", [])]


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

    def fetch_embeddings(self, limit: int | None, force: bool = False, expected_bytes: int | None = None) -> list[dict]:
        if force:
            where_clause = ""
        elif expected_bytes:
            where_clause = f"WHERE sd.embedding IS NULL OR length(sd.embedding) != {expected_bytes}"
        else:
            where_clause = "WHERE sd.embedding IS NULL"

        sql = f"SELECT sd.id, sd.ai_line, sd.user_model_answer, cu.topic_tags FROM sample_dialogues sd JOIN content_units cu ON sd.content_unit_id = cu.id {where_clause}"  # nosec B608
        if limit:
            sql += f" LIMIT {limit}"
        return [dict(r) for r in self.conn.execute(sql).fetchall()]

    def fetch_null_embeddings(self, limit: int | None = None, force: bool = False, expected_bytes: int | None = None) -> list[dict]:
        return self.fetch_embeddings(limit=limit, force=force, expected_bytes=expected_bytes)

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

    def fetch_embeddings(self, limit: int | None, force: bool = False, expected_bytes: int | None = None):
        if force:
            where_clause = ""
        elif expected_bytes:
            where_clause = f"WHERE sd.embedding IS NULL OR length(sd.embedding) != {expected_bytes}"
        else:
            where_clause = "WHERE sd.embedding IS NULL"

        sql = f"SELECT sd.id, sd.ai_line, sd.user_model_answer, cu.topic_tags FROM sample_dialogues sd JOIN content_units cu ON sd.content_unit_id = cu.id {where_clause}"  # nosec B608
        if limit:
            sql += f" LIMIT {limit}"
        result = self.client.execute(sql)
        return [dict(zip(result.columns, row)) for row in result.rows]

    def fetch_null_embeddings(self, limit: int | None = None, force: bool = False, expected_bytes: int | None = None):
        return self.fetch_embeddings(limit=limit, force=force, expected_bytes=expected_bytes)

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
    ap.add_argument("--backend", choices=["openai", "local", "gemini"], required=True,
                    help="Embedding backend: openai (1536d), local (384d), gemini (3072d)")
    ap.add_argument("--model", type=str, default="gemini-embedding-2",
                    help="Tên model (Mặc định: gemini-embedding-2 cho Gemini, text-embedding-3-small cho OpenAI)")
    ap.add_argument("--sqlite", type=str, metavar="DB_PATH")
    ap.add_argument("--turso-url", type=str)
    ap.add_argument("--turso-token", type=str)
    ap.add_argument("--batch-size", type=int, default=32,
                    help="Số row embed mỗi batch API call (default 32)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Chỉ xử lý N row đầu (để test)")
    ap.add_argument("--force", action="store_true",
                    help="Ghi đè embedding hiện có (dùng khi chuyển đổi model embedding)")
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

    # Tính expected byte size để tự động detect các dòng chưa được re-embed bằng model hiện tại
    expected_bytes = 12288 if args.backend == "gemini" else (6144 if args.backend == "openai" else 1536)

    # Lấy danh sách row cần embed
    rows = db.fetch_embeddings(args.limit, force=args.force, expected_bytes=expected_bytes)
    if not rows:
        print("Không có row nào cần embed (embedding đã đầy đủ). Dùng --force nếu muốn ghi đè toàn bộ.")
        return


    model_name = args.model if args.backend == "gemini" else ("text-embedding-3-small" if args.backend == "openai" else "all-MiniLM-L6-v2")
    print(f"Cần embed: {len(rows)} rows | backend: {args.backend} ({model_name}) | batch: {args.batch_size}")

    if args.backend == "openai":
        def embed_fn(t: list[str]) -> list[list[float]]:
            return embed_openai(t, model=model_name)
    elif args.backend == "gemini":
        gemini_pool = GeminiKeyPool()
        print(f"[Gemini Multi-Key] Đã load {len(gemini_pool.keys)} API Key(s) từ .env")
        def embed_fn(t: list[str]) -> list[list[float]]:
            return embed_gemini(t, key_pool=gemini_pool, model=model_name)
    else:
        embed_fn = embed_local

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

        # Pacing rate limit cho Gemini và OpenAI (tránh chạm trần RPM 100)
        if i + args.batch_size < len(rows):
            if args.backend == "gemini":
                time.sleep(0.7)  # Giữ tốc độ ~85 RPM, an toàn tuyệt đối dưới ngưỡng 100 RPM
            elif args.backend == "openai":
                time.sleep(0.5)


    db.close()
    print(f"\n{'='*60}")
    print(f"Hoàn thành: {processed}/{len(rows)} rows đã có embedding")
    print('='*60)


if __name__ == "__main__":
    main()
