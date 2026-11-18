import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sources TEXT,
                    workflow_metadata TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    conversation_id TEXT
                )
            """)
            cursor.execute("PRAGMA table_info(documents)")
            columns = [col[1] for col in cursor.fetchall()]
            if "conversation_id" not in columns:
                try:
                    cursor.execute("ALTER TABLE documents ADD COLUMN conversation_id TEXT")
                except Exception:
                    pass
            conn.commit()

    @contextmanager
    def get_connection(self):
        with self.lock:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
