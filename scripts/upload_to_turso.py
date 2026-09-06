"""
Upload/Sync Local SQLite Database (data/custom_topics.db) to Turso Cloud DB
Usage:
    python scripts/upload_to_turso.py --turso-url libsql://<db-name>-<user>.turso.io --turso-token <auth-token>
"""

import argparse
import os
import sqlite3
import sys
import time

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import libsql_experimental as libsql
    HAS_LIBSQL = True
except ImportError:
    HAS_LIBSQL = False


def sync_local_to_turso(turso_url: str, turso_token: str, local_db_path: str = "data/custom_topics.db"):
    if not HAS_LIBSQL:
        print("[Error] libsql-experimental is not installed. Run: pip install libsql-experimental", flush=True)
        sys.exit(1)

    if not os.path.exists(local_db_path):
        print(f"[Error] Local database file not found at: {local_db_path}", flush=True)
        sys.exit(1)

    print(f"[*] Reading local SQLite database: {local_db_path}...", flush=True)
    local_conn = sqlite3.connect(local_db_path)
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()

    print(f"[*] Connecting to Turso Cloud Database: {turso_url}...", flush=True)

    def get_remote_conn():
        conn = libsql.connect(database=turso_url, auth_token=turso_token)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        return conn

    try:
        remote_conn = get_remote_conn()
        remote_cursor = remote_conn.cursor()
    except Exception as e:
        print(f"[Error] Failed to connect to Turso: {e}", flush=True)
        sys.exit(1)

    # 1. Initialize schema on Turso
    from app.storage.db import init_db
    os.environ["TURSO_DATABASE_URL"] = turso_url
    os.environ["TURSO_AUTH_TOKEN"] = turso_token
    init_db()

    # 2. Get list of tables in local db
    local_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row["name"] for row in local_cursor.fetchall()]
    print(f"[*] Found {len(tables)} tables to sync: {', '.join(tables)}\n", flush=True)

    for table in tables:
        local_cursor.execute(f"SELECT * FROM {table}")  # nosec B608

        rows = local_cursor.fetchall()
        total_rows = len(rows)
        if total_rows == 0:
            print(f"  - [{table}]: 0 rows (skipped)", flush=True)
            continue

        col_names = [col[0] for col in local_cursor.description]
        cols_str = ", ".join(col_names)
        num_cols = len(col_names)

        # Batch insert chunks (keeping total params <= 900 to stay safely within SQLite parameter limits)
        batch_size = max(1, min(100, 900 // max(1, num_cols)))
        count = 0

        for i in range(0, total_rows, batch_size):
            chunk = rows[i:i + batch_size]
            row_placeholders = f"({', '.join(['?'] * num_cols)})"
            all_placeholders = ", ".join([row_placeholders] * len(chunk))
            insert_query = f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES {all_placeholders}"

            flat_values = []
            for r in chunk:
                for col in col_names:
                    flat_values.append(r[col])

            params_tuple = tuple(flat_values)

            # Auto-retry with stream renewal if Hrana stream expires
            for attempt in range(3):
                try:
                    remote_cursor.execute(insert_query, params_tuple)
                    remote_conn.commit()
                    break
                except Exception:
                    if attempt < 2:
                        time.sleep(1)
                        try:
                            remote_conn = get_remote_conn()
                            remote_cursor = remote_conn.cursor()
                        except Exception:
                            pass
                    else:
                        raise


            count += len(chunk)
            if total_rows > 200 and (count % 500 == 0 or count == total_rows):
                print(f"  - [{table}]: Progress {count}/{total_rows} rows...", flush=True)

        print(f"  - [{table}]: Successfully synced all {total_rows} rows -> Turso", flush=True)

    print("\n[SUCCESS] All data has been synced to Turso Cloud Database!", flush=True)
    local_conn.close()
    try:
        remote_conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync local SQLite DB to Turso Cloud")
    parser.add_argument("--turso-url", default=os.getenv("TURSO_DATABASE_URL", ""), help="Turso Database URL (libsql://...)")
    parser.add_argument("--turso-token", default=os.getenv("TURSO_AUTH_TOKEN", ""), help="Turso Auth Token")
    parser.add_argument("--db-path", default="data/custom_topics.db", help="Path to local sqlite database")

    args = parser.parse_args()

    if not args.turso_url or not args.turso_token:
        print("[Error] Missing --turso-url or --turso-token arguments.", flush=True)
        print("Usage: python scripts/upload_to_turso.py --turso-url libsql://... --turso-token ...", flush=True)
        sys.exit(1)

    sync_local_to_turso(args.turso_url, args.turso_token, args.db_path)
