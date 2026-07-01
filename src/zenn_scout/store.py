import json
from datetime import datetime, timezone
from .db import get_conn


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_author(username: str, user: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO authors (username, name, follower_count, articles_count, fetched_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                name           = excluded.name,
                follower_count = excluded.follower_count,
                articles_count = excluded.articles_count,
                fetched_at     = excluded.fetched_at
            """,
            (
                username,
                user.get("name", ""),
                user.get("follower_count", 0),
                user.get("articles_count", 0),
                now(),
            ),
        )


def upsert_article(article: dict, body_text: str = "", extra_topics: list[str] | None = None) -> None:
    raw_topics = [t["name"] for t in article.get("topics", [])]
    if not raw_topics and extra_topics:
        raw_topics = extra_topics
    topics = json.dumps(raw_topics, ensure_ascii=False)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO articles
                (slug, title, body_text, liked_count, bookmarks_count,
                 published_at, updated_at, author_username, topics, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                title           = excluded.title,
                body_text       = CASE WHEN excluded.body_text != '' THEN excluded.body_text ELSE body_text END,
                liked_count     = excluded.liked_count,
                bookmarks_count = excluded.bookmarks_count,
                updated_at      = excluded.updated_at,
                topics          = (
                    SELECT json_group_array(DISTINCT value)
                    FROM (
                        SELECT value FROM json_each(topics)
                        UNION
                        SELECT value FROM json_each(excluded.topics)
                    )
                ),
                fetched_at      = excluded.fetched_at
            """,
            (
                article["slug"],
                article["title"],
                body_text,
                article.get("liked_count", 0),
                article.get("bookmarked_count", 0),
                article.get("published_at", ""),
                article.get("body_updated_at", ""),
                article.get("user", {}).get("username", ""),
                topics,
                now(),
            ),
        )
