import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = os.environ.get(
    "AUTH_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth.db")
)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                client_name TEXT NOT NULL,
                tier TEXT NOT NULL DEFAULT 'standard',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                total_requests INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()

        # Seed default demo testing key if no keys exist
        cursor.execute("SELECT COUNT(*) as count FROM api_keys")
        count = cursor.fetchone()["count"]
        if count == 0:
            default_key = "gdg-test-key-2026"
            cursor.execute(
                """
                INSERT INTO api_keys (api_key, client_name, tier, is_active, created_at, total_requests)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    default_key,
                    "Demo Developer Client",
                    "enterprise",
                    1,
                    datetime.utcnow().isoformat(),
                    0,
                ),
            )
            conn.commit()


# Initialize upon module load
init_db()
