import sqlite3
from typing import List, Dict, Any, Optional

DB_FILE = "mock_platform.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Channels
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        channel_type TEXT NOT NULL,
        description TEXT
    );
    """)

    # 2. Posts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT NOT NULL,
        campaign_week INTEGER NOT NULL DEFAULT 1,
        content TEXT NOT NULL,
        creative_brief TEXT,
        scheduled_hour INTEGER,
        status TEXT DEFAULT 'draft',
        FOREIGN KEY(channel_id) REFERENCES channels(id)
    );
    """)

    post_columns = {row[1] for row in cursor.execute("PRAGMA table_info(posts)")}
    if "campaign_week" not in post_columns:
        cursor.execute(
            "ALTER TABLE posts ADD COLUMN campaign_week INTEGER NOT NULL DEFAULT 1"
        )

    # 3. Post Metrics
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS post_metrics (
        post_id INTEGER PRIMARY KEY,
        impressions INTEGER DEFAULT 0,
        likes INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        shares INTEGER DEFAULT 0,
        engagement_rate REAL DEFAULT 0,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    );
    """)

    # Upgrade databases created before engagement_rate was added.
    metric_columns = {row[1] for row in cursor.execute("PRAGMA table_info(post_metrics)")}
    if "engagement_rate" not in metric_columns:
        cursor.execute(
            "ALTER TABLE post_metrics ADD COLUMN engagement_rate REAL NOT NULL DEFAULT 0"
        )

    # 4. Comments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        author TEXT,
        text TEXT NOT NULL,
        sentiment TEXT,
        agent_reply TEXT,
        FOREIGN KEY(post_id) REFERENCES posts(id)
    );
    """)

    # Seed Default Channels
    channels = [
        ("Static_image", "microblog","Engaging","High churn, questions do well"),
        ("Short_video", "InstaVibe", "visual", "Lifestyle imagery, visual hooks, moderate caption"),
        ("Blog_post", "B2BNetwork", "professional", "Thought leadership, case studies, high substance")
    ]
    cursor.executemany("INSERT OR IGNORE INTO channels VALUES (?, ?, ?, ?)", channels)
    conn.commit()
    conn.close()
    print("Database initialized with 3 channels.")

if __name__ == "__main__":
    init_db()