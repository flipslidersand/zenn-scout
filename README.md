# zenn-scout

A crawler and data collection tool for Zenn articles. Fetches trending articles, topic-specific articles, and author information, then stores them in SQLite.

Zenn 記事の巡回・データ収集ツール。人気記事・トピック別記事・著者情報を SQLite に保存する。

## Setup / セットアップ

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage / 使い方

```bash
# Fetch 100 trending articles (with body text and author info)
# 人気記事を 100 件取得（本文・著者情報込み）
zenn-scout fetch --pages 5 --body --author

# Filter by topic / トピック指定
zenn-scout fetch --topics rust,go,python --pages 3

# Sort by latest / 最新順
zenn-scout fetch --topics ai --order latest --pages 2

# Search the DB / DB 検索
zenn-scout query --topic rust --min-likes 50
zenn-scout query --author username --limit 10 --json

# Show statistics / 統計
zenn-scout stats
```

## Schema / スキーマ

| Table / テーブル | Key columns / 主なカラム |
| ---------------- | ------------------------- |
| `articles` | slug, title, body_text, liked_count, bookmarks_count, topics, author_username |
| `authors`  | username, name, follower_count, articles_count |
