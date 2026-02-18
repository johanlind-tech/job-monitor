import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "seen_jobs.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            url TEXT,
            source TEXT,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def is_seen(job_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT 1 FROM seen_jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return row is not None


def mark_seen(job: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO seen_jobs (id, title, company, url, source) VALUES (?, ?, ?, ?, ?)",
        (job["id"], job["title"], job.get("company", ""), job["url"], job["source"]),
    )
    conn.commit()
    conn.close()
