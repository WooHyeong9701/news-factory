import sqlite3
import os
from models.news import NewsItem

class NewsDatabase:
    def __init__(self, db_path="news.db"):
        self.db_path = db_path
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_table(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    snippet TEXT,
                    publisher TEXT,
                    published_at TEXT,
                    url TEXT UNIQUE,
                    full_content TEXT,
                    comment_count INTEGER DEFAULT 0,
                    reaction_count INTEGER DEFAULT 0,
                    reaction_detail TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def insert_news(self, news_item: NewsItem):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO news 
                    (title, snippet, publisher, published_at, url, full_content, comment_count, reaction_count, reaction_detail) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    news_item.title,
                    news_item.snippet,
                    news_item.publisher,
                    news_item.published_at,
                    news_item.url,
                    news_item.full_content,
                    news_item.comment_count,
                    news_item.reaction_count,
                    news_item.reaction_detail
                ))
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    def get_all_news(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM news ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
