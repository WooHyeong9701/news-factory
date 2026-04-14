import sqlite3

def migrate():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    # 1. Create issue table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS issue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            representative_title TEXT NOT NULL,
            first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    """)
    
    # 2. Add columns to news table
    cols_news = {
        "issue_id": "INTEGER REFERENCES issue(id)",
        "comment_count": "INTEGER DEFAULT 0",
        "reaction_count": "INTEGER DEFAULT 0",
        "reaction_detail": "TEXT",
        "full_content": "TEXT"
    }
    
    for col, spec in cols_news.items():
        try:
            cursor.execute(f"ALTER TABLE news ADD COLUMN {col} {spec}")
            print(f"Added {col} to news table.")
        except sqlite3.OperationalError:
            pass

    # 3. Add columns to issue table
    cols_issue = {
        "summary_candidate": "TEXT",
        "title_candidates": "TEXT", # JSON string
        "image_paths": "TEXT",      # JSON string
        "selected_title": "TEXT",
        "selected_image": "TEXT",
        "is_published": "INTEGER DEFAULT 0"
    }
    
    for col, spec in cols_issue.items():
        try:
            cursor.execute(f"ALTER TABLE issue ADD COLUMN {col} {spec}")
            print(f"Added {col} to issue table.")
        except sqlite3.OperationalError:
            pass
        
    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
