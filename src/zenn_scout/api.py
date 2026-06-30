import time
import httpx
from typing import Any

BASE = "https://zenn.dev/api"
HEADERS = {"User-Agent": "zenn-scout/1.0 (github.com/flipslidersand/zenn-scout)"}


def _get(path: str, params: dict | None = None) -> Any:
    url = f"{BASE}{path}"
    r = httpx.get(url, params=params, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()


def fetch_articles(
    *,
    order: str = "liked",
    topic: str | None = None,
    username: str | None = None,
    count: int = 20,
    page: int = 1,
) -> list[dict]:
    params: dict = {"order": order, "count": count, "page": page}
    if topic:
        params["topic_name"] = topic
    if username:
        params["username"] = username
    data = _get("/articles", params)
    return data.get("articles", [])


def fetch_article_detail(slug: str) -> dict:
    """個別記事を取得（topics・body_html 含む）"""
    try:
        data = _get(f"/articles/{slug}")
        return data.get("article", {})
    except Exception:
        return {}


def fetch_user(username: str) -> dict:
    try:
        data = _get(f"/users/{username}")
        return data.get("user", {})
    except Exception:
        return {}


def fetch_all_articles(
    *,
    order: str = "liked",
    topic: str | None = None,
    username: str | None = None,
    max_pages: int = 5,
    delay: float = 0.5,
) -> list[dict]:
    results = []
    for page in range(1, max_pages + 1):
        batch = fetch_articles(
            order=order, topic=topic, username=username, count=20, page=page
        )
        if not batch:
            break
        results.extend(batch)
        time.sleep(delay)
    return results
