import argparse
import json
import sys
import time
from .db import init_db, get_conn
from .api import fetch_all_articles, fetch_article_detail, fetch_user
from .store import upsert_article, upsert_author


def cmd_fetch(args: argparse.Namespace) -> None:
    init_db()
    topics = [t.strip() for t in args.topics.split(",")] if args.topics else [None]

    total = 0
    for topic in topics:
        label = topic or "popular"
        print(f"[fetch] topic={label} order={args.order} max_pages={args.pages}")
        articles = fetch_all_articles(
            order=args.order,
            topic=topic,
            max_pages=args.pages,
            delay=args.delay,
        )
        print(f"  取得: {len(articles)} 件")

        for i, article in enumerate(articles, 1):
            slug = article["slug"]
            body = ""
            if args.body:
                detail = fetch_article_detail(slug)
                body = detail.get("body_html", "")
                # detail には topics も含まれるので article にマージ
                if detail.get("topics"):
                    article = {**article, "topics": detail["topics"]}
                time.sleep(args.delay)

            upsert_article(article, body, extra_topics=[topic] if topic else None)

            username = article.get("user", {}).get("username", "")
            if username and args.author:
                user = fetch_user(username)
                if user:
                    upsert_author(username, user)
                time.sleep(args.delay)

            if i % 10 == 0:
                print(f"  保存済み: {i}/{len(articles)}")

        total += len(articles)

    print(f"完了: 合計 {total} 件保存")


def cmd_query(args: argparse.Namespace) -> None:
    init_db()
    with get_conn() as conn:
        wheres = []
        params: list = []

        if args.topic:
            wheres.append("topics LIKE ?")
            params.append(f'%"{args.topic}"%')
        if args.author:
            wheres.append("author_username = ?")
            params.append(args.author)
        if args.min_likes:
            wheres.append("liked_count >= ?")
            params.append(args.min_likes)

        where_clause = f"WHERE {' AND '.join(wheres)}" if wheres else ""
        sql = f"""
            SELECT slug, title, liked_count, bookmarks_count, author_username, topics
            FROM articles
            {where_clause}
            ORDER BY liked_count DESC
            LIMIT ?
        """
        params.append(args.limit)

        rows = conn.execute(sql, params).fetchall()

    if args.json:
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
    else:
        print(f"{'slug':<40} {'likes':>6} {'bm':>6}  title")
        print("-" * 80)
        for r in rows:
            print(f"{r['slug']:<40} {r['liked_count']:>6} {r['bookmarks_count']:>6}  {r['title'][:40]}")


def cmd_stats(args: argparse.Namespace) -> None:
    init_db()
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        authors = conn.execute("SELECT COUNT(*) FROM authors").fetchone()[0]
        top = conn.execute(
            "SELECT title, liked_count, author_username FROM articles ORDER BY liked_count DESC LIMIT 5"
        ).fetchall()

    print(f"記事数: {total}  著者数: {authors}")
    print("\nTop 5 (いいね):")
    for r in top:
        print(f"  {r['liked_count']:>6}  @{r['author_username']}  {r['title'][:50]}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="zenn-scout")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # fetch
    p_fetch = sub.add_parser("fetch", help="記事を取得して保存")
    p_fetch.add_argument("--topics", help="カンマ区切りトピック (例: rust,go,python)")
    p_fetch.add_argument("--order", default="liked", choices=["liked", "latest"])
    p_fetch.add_argument("--pages", type=int, default=5, help="取得ページ数 (20件/page)")
    p_fetch.add_argument("--body", action="store_true", help="本文テキストも取得")
    p_fetch.add_argument("--author", action="store_true", help="著者情報も取得")
    p_fetch.add_argument("--delay", type=float, default=0.5, help="リクエスト間隔(秒)")

    # query
    p_query = sub.add_parser("query", help="DBを検索")
    p_query.add_argument("--topic", help="トピックで絞り込み")
    p_query.add_argument("--author", help="著者名で絞り込み")
    p_query.add_argument("--min-likes", type=int, default=0)
    p_query.add_argument("--limit", type=int, default=20)
    p_query.add_argument("--json", action="store_true")

    # stats
    sub.add_parser("stats", help="DB統計を表示")

    args = parser.parse_args()
    {"fetch": cmd_fetch, "query": cmd_query, "stats": cmd_stats}[args.cmd](args)


if __name__ == "__main__":
    main()
