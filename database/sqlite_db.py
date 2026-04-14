import sqlite3
import os
import json
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
                    issue_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (issue_id) REFERENCES issue (id)
                )
            """)
            
            # Create issue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS issue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    representative_title TEXT NOT NULL,
                    summary_candidate TEXT,
                    title_candidates TEXT, -- JSON string of 3 titles
                    image_paths TEXT,      -- JSON string of image URLs/paths
                    selected_title TEXT,
                    selected_image TEXT,
                    is_published INTEGER DEFAULT 0,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)
            conn.commit()

    def insert_news(self, news_item: NewsItem):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO news 
                    (title, snippet, publisher, published_at, url, full_content, comment_count, reaction_count, reaction_detail, issue_id) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    news_item.title,
                    news_item.snippet,
                    news_item.publisher,
                    news_item.published_at,
                    news_item.url,
                    news_item.full_content,
                    news_item.comment_count,
                    news_item.reaction_count,
                    news_item.reaction_detail,
                    news_item.issue_id
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

    def create_issue(self, representative_title: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO issue (representative_title) VALUES (?)", (representative_title,))
            conn.commit()
            return cursor.lastrowid

    def get_active_issues(self, hours=24):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM issue 
                WHERE status = 'active' 
                AND first_seen_at >= datetime('now', ?)
            """, (f'-{hours} hours',))
            return [dict(row) for row in cursor.fetchall()]

    def update_news_issue(self, news_id: int, issue_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE news SET issue_id = ? WHERE id = ?", (issue_id, news_id))
            conn.commit()

    def mark_issue_published(self, issue_id: int, title: str, image: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE issue 
                SET selected_title = ?, selected_image = ?, is_published = 1 
                WHERE id = ?
            """, (title, image, issue_id))
            conn.commit()

    def get_issue_by_id(self, issue_id: int):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM issue WHERE id = ?", (issue_id,))
            res = cursor.fetchone()
            return dict(res) if res else None

    def update_issue_candidates(self, issue_id: int, summary: str, titles: list, images: list):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE issue 
                SET summary_candidate = ?, title_candidates = ?, image_paths = ? 
                WHERE id = ?
            """, (summary, json.dumps(titles, ensure_ascii=False), json.dumps(images, ensure_ascii=False), issue_id))
            conn.commit()

    def get_issues_with_candidates(self, limit=10):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM issue 
                WHERE summary_candidate IS NOT NULL 
                ORDER BY first_seen_at DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_issue_stats(self, issue_id: int):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as article_count,
                    SUM(comment_count) as total_comments,
                    SUM(reaction_count) as total_reactions,
                    MIN(created_at) as first_seen,
                    MAX(created_at) as last_seen
                FROM news 
                WHERE issue_id = ?
            """, (issue_id,))
            return dict(cursor.fetchone())

    def delete_issue(self, issue_id: int):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Delete associated news
            cursor.execute("DELETE FROM news WHERE issue_id = ?", (issue_id,))
            # 2. Delete the issue itself
            cursor.execute("DELETE FROM issue WHERE id = ?", (issue_id,))
            conn.commit()
