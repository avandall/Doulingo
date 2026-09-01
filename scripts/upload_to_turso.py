"""
Upload/Sync Local SQLite Database (data/custom_topics.db) to Turso Cloud DB
Usage:
    python scripts/upload_to_turso.py --turso-url libsql://<db-name>-<user>.turso.io --turso-token <auth-token>
"""

import argparse
import os
import sqlite3
import sys

try:
    import libsql_experimental as libsql
    HAS_LIBSQL = True
except ImportError:
    HAS_LIBSQL = False


def sync_local_to_turso(turso_url: str, turso_token: str, local_db_path: str = "data/custom_topics.db"):
    if not HAS_LIBSQL:
        print("[Error] libsql-experimental is not installed. Run: pip install libsql-experimental")
        sys.exit(1)

    if not os.path.exists(local_db_path):
        print(f"[Error] Local database file not found at: {local_db_path}")
        sys.exit(1)

    print(f"[*] Reading local SQLite database: {local_db_path}...")
    local_conn = sqlite3.connect(local_db_path)
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()

    print(f"[*] Connecting to Turso Cloud Database: {turso_url}...")
    try:
        remote_conn = libsql.connect(database=turso_url, auth_token=turso_token)
        remote_cursor = remote_conn.cursor()
        remote_cursor.execute("SELECT 1")
    except Exception as e:
        print(f"[Error] Failed to connect to Turso: {e}")
        sys.exit(1)

    # 1. Initialize schema on Turso
    from app.storage.db import init_db
    # Temporary set env for init_db
    os.environ["TURSO_DATABASE_URL"] = turso_url
    os.environ["TURSO_AUTH_TOKEN"] = turso_token
    init_db()

    # 2. Get list of tables in local db
    local_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row["name"] for row in local_cursor.fetchall()]
    print(f"[*] Found {len(tables)} tables to sync: {', '.join(tables)}")

    for table in tables:
        local_cursor.execute(f"SELECT * FROM {table}")
        rows = local_cursor.fetchall()
        if not rows:
            print(f"  - [{table}]: 0 rows (skipped)")
            continue

        col_names = [col[0] for col in local_cursor.description]
        placeholders = ", ".join(["?"] * len(col_names))
        cols_str = ", ".join(col_names)
        insert_query = f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders})"

        count = 0
        for r in rows:
            values = [r[col] for col in col_names]
            remote_cursor.execute(insert_query, values)
            count += 1

        remote_conn.commit()
        print(f"  - [{table}]: Successfully synced {count} rows -> Turso")

    print("\n[SUCCESS] All data has been synced to Turso Cloud Database!")
    local_conn.close()
    remote_conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync local SQLite DB to Turso Cloud")
    parser.add_argument("--turso-url", default=os.getenv("TURSO_DATABASE_URL", ""), help="Turso Database URL (libsql://...)")
    parser.add_argument("--turso-token", default=os.getenv("TURSO_AUTH_TOKEN", ""), help="Turso Auth Token")
    parser.add_argument("--db-path", default="data/custom_topics.db", help="Path to local sqlite database")

    args = parser.parse_args()

    if not args.turso_url or not args.turso_token:
        print("[Error] Missing --turso-url or --turso-token arguments.")
        print("Usage: python scripts/upload_to_turso.py --turso-url libsql://... --turso-token ...")
        sys.exit(1)

    sync_local_to_turso(args.turso_url, args.turso_token, args.db_path)
