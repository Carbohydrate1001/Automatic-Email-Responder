"""
Database initialization and connection management.
Uses Python's built-in sqlite3 module.
"""

import sqlite3
import contextlib
from config import Config


def _ensure_column(conn, table_name: str, column_name: str, column_def: str):
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


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
                retry_count INTEGER DEFAULT 0,
                last_error  TEXT,
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

            CREATE TABLE IF NOT EXISTS feedback_records (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id              INTEGER NOT NULL REFERENCES emails(id) ON DELETE CASCADE,
                reply_id              INTEGER REFERENCES replies(id),
                action                TEXT NOT NULL,
                original_category     TEXT,
                corrected_category    TEXT,
                original_reply_text   TEXT,
                edited_reply_text     TEXT,
                operator              TEXT,
                notes                 TEXT,
                created_at            TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_feedback_email_id ON feedback_records(email_id);
            CREATE INDEX IF NOT EXISTS idx_feedback_action ON feedback_records(action);
            CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback_records(original_category, corrected_category);

            CREATE TABLE IF NOT EXISTS few_shot_examples (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT NOT NULL,
                label       TEXT NOT NULL DEFAULT 'POSITIVE',
                subject     TEXT NOT NULL,
                body        TEXT NOT NULL,
                source      TEXT DEFAULT 'manual',
                note        TEXT,
                is_active   INTEGER DEFAULT 1,
                created_by  TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_few_shot_category ON few_shot_examples(category, label, is_active);

            CREATE TABLE IF NOT EXISTS products (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name            TEXT UNIQUE NOT NULL,
                unit_price              REAL NOT NULL,
                currency                TEXT DEFAULT 'USD',
                min_order_quantity      INTEGER NOT NULL,
                delivery_lead_time_days INTEGER NOT NULL,
                aliases                 TEXT,
                description             TEXT,
                is_active               INTEGER DEFAULT 1,
                created_at              TEXT DEFAULT (datetime('now')),
                updated_at              TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS customers (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                email_address       TEXT UNIQUE NOT NULL,
                display_name        TEXT,
                preferred_language  TEXT DEFAULT 'unknown',
                contact_count       INTEGER DEFAULT 0,
                last_contact_at     TEXT,
                common_categories   TEXT,
                notes               TEXT,
                created_at          TEXT DEFAULT (datetime('now')),
                updated_at          TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email_address);
        """)

        # Backwards-compatible column additions for existing databases
        _ensure_column(conn, "emails", "retry_count",     "INTEGER DEFAULT 0")
        _ensure_column(conn, "emails", "last_error",      "TEXT")
        _ensure_column(conn, "emails", "language",        "TEXT DEFAULT 'unknown'")
        _ensure_column(conn, "emails", "is_read",         "INTEGER DEFAULT 0")
        _ensure_column(conn, "emails", "human_category",  "TEXT")
        _ensure_column(conn, "emails", "feedback",        "TEXT")

        _ensure_column(conn, "replies", "feedback_score", "INTEGER")
        _ensure_column(conn, "replies", "edited_text",    "TEXT")

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
