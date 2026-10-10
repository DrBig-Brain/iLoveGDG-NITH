import secrets
from datetime import datetime
from typing import Optional, List, Dict, Any
from .database import get_connection


def generate_secure_key(prefix: str = "gdg_live_") -> str:
    random_bytes = secrets.token_urlsafe(24)
    return f"{prefix}{random_bytes}"


def create_api_key(client_name: str, tier: str = "standard") -> Dict[str, Any]:
    api_key = generate_secure_key()
    created_at = datetime.utcnow().isoformat()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO api_keys (api_key, client_name, tier, is_active, created_at, total_requests)
            VALUES (?, ?, ?, 1, ?, 0)
            """,
            (api_key, client_name, tier, created_at),
        )
        conn.commit()
        key_id = cursor.lastrowid
        return {
            "id": key_id,
            "api_key": api_key,
            "client_name": client_name,
            "tier": tier,
            "is_active": True,
            "created_at": created_at,
            "total_requests": 0,
        }


def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    if not api_key:
        return None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM api_keys WHERE api_key = ? AND is_active = 1",
            (api_key.strip(),),
        )
        row = cursor.fetchone()
        if not row:
            return None

        # Increment total requests counter
        cursor.execute(
            "UPDATE api_keys SET total_requests = total_requests + 1 WHERE id = ?",
            (row["id"],),
        )
        conn.commit()

        return {
            "id": row["id"],
            "api_key": row["api_key"],
            "client_name": row["client_name"],
            "tier": row["tier"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
            "total_requests": row["total_requests"] + 1,
        }


def revoke_api_key(api_key: str) -> bool:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE api_keys SET is_active = 0 WHERE api_key = ?",
            (api_key.strip(),),
        )
        conn.commit()
        return cursor.rowcount > 0


def list_api_keys() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM api_keys ORDER BY id DESC")
        rows = cursor.fetchall()
        return [
            {
                "id": r["id"],
                "api_key": f"{r['api_key'][:8]}...{r['api_key'][-4:]}" if len(r['api_key']) > 12 else r['api_key'],
                "client_name": r["client_name"],
                "tier": r["tier"],
                "is_active": bool(r["is_active"]),
                "created_at": r["created_at"],
                "total_requests": r["total_requests"],
            }
            for r in rows
        ]
