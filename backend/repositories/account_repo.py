from typing import Optional, List, Dict, Any
from ..core.database import get_db_connection

class AccountRepository:
    @staticmethod
    def get(account_id: int) -> Optional[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE account_id = ?", (account_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT account_id, email, name, picture, connected_at, expires_at FROM accounts")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def save_token(
        account_id: int,
        email: str,
        name: str,
        picture: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: float
    ) -> None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO accounts (account_id, email, name, picture, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id) DO UPDATE SET
                email=excluded.email,
                name=excluded.name,
                picture=excluded.picture,
                access_token=excluded.access_token,
                refresh_token=COALESCE(excluded.refresh_token, accounts.refresh_token),
                expires_at=excluded.expires_at,
                connected_at=CURRENT_TIMESTAMP
            """, (account_id, email, name, picture, access_token, refresh_token, expires_at))

    @staticmethod
    def remove(account_id: int) -> None:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts WHERE account_id = ?", (account_id,))
            cursor.execute("DELETE FROM photos WHERE account_id = ?", (account_id,))
            cursor.execute("""
            DELETE FROM matches
            WHERE photo_id_1 NOT IN (SELECT id FROM photos)
               OR photo_id_2 NOT IN (SELECT id FROM photos)
            """)
