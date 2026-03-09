"""
Database initialization and connection management.
Uses Python's built-in sqlite3 module.
"""

import sqlite3
import contextlib
from config import Config


def init_db():
    """Create all tables if they don't exist (idempotent)."""
    with get_db_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS emails (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id  TEXT UNIQUE NOT NULL,
                subject     TEXT,
                sender      TEXT,
                received_at TEXT,
                body        TEXT,
                category    TEXT,
                confidence  REAL,
                reasoning   TEXT,
                status      TEXT DEFAULT 'pending_review',
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS replies (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id    INTEGER REFERENCES emails(id),
                reply_text  TEXT,
                sent_at     TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id    INTEGER REFERENCES emails(id),
                action      TEXT,
                operator    TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()


@contextlib.contextmanager
def get_db_connection():
    """Context manager that yields a sqlite3 connection and closes it on exit."""
    conn = sqlite3.connect(Config.DATABASE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
