
import sqlite3
from pathlib import Path

DB_PATH = Path("data/career_agent.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                internship_id TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT,
                match_score REAL,
                apply_url TEXT,
                status TEXT NOT NULL DEFAULT 'Shortlisted',
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(internship_id)
            )
        """)

        connection.commit()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DB_PATH}")
