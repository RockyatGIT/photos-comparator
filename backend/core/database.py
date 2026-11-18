import sqlite3
from contextlib import contextmanager
from typing import Generator
from .config import settings

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database connection lifecycle."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Idempotently initialize all database tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER PRIMARY KEY, -- 1 or 2
            email TEXT,
            name TEXT,
            picture TEXT,
            access_token TEXT,
            refresh_token TEXT,
            expires_at REAL,
            connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            google_id TEXT NOT NULL,
            filename TEXT,
            mime_type TEXT,
            base_url TEXT,
            thumbnail_path TEXT,
            creation_time TEXT,
            width INTEGER,
            height INTEGER,
            camera_make TEXT,
            camera_model TEXT,
            phash TEXT,
            dhash TEXT,
            ahash TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id, google_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photo_id_1 INTEGER NOT NULL,
            photo_id_2 INTEGER NOT NULL,
            phash_distance INTEGER NOT NULL,
            similarity_score REAL NOT NULL,
            match_type TEXT NOT NULL, -- 'exact', 'duplicate', 'similar'
            time_diff_seconds REAL,
            dismissed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(photo_id_1, photo_id_2)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

init_db()
