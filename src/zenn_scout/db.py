import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "zenn.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS authors (
                username        TEXT PRIMARY KEY,
                name            TEXT,
                follower_count  INTEGER DEFAULT 0,
                articles_count  INTEGER DEFAULT 0,
                fetched_at      TEXT
            );

            CREATE TABLE IF NOT EXISTS articles (
                slug            TEXT PRIMARY KEY,
                title           TEXT NOT NULL,
                body_text       TEXT,
                liked_count     INTEGER DEFAULT 0,
                bookmarks_count INTEGER DEFAULT 0,
                published_at    TEXT,
                updated_at      TEXT,
                author_username TEXT,
                topics          TEXT,
                fetched_at      TEXT,
                FOREIGN KEY (author_username) REFERENCES authors(username)
            );

            CREATE INDEX IF NOT EXISTS idx_articles_liked  ON articles(liked_count DESC);
            CREATE INDEX IF NOT EXISTS idx_articles_author ON articles(author_username);
            CREATE INDEX IF NOT EXISTS idx_articles_topics ON articles(topics);
        """)
