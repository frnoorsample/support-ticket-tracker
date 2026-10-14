"""Database setup using Python's built-in sqlite3 module.

Every query in this project uses parameterised placeholders (?) rather than
string formatting, which prevents SQL injection.
"""
import sqlite3

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    description TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    priority    TEXT    NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
    status      TEXT    NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    created_by  INTEGER NOT NULL REFERENCES users(id),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # lets us read columns by name, like a dictionary
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite needs this to enforce REFERENCES
    return conn


def init_db() -> None:
    """Create the tables if they don't already exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def get_db():
    """Gives each request its own connection, and always closes it afterwards."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()