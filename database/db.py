import json
import sqlite3
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "scamshield.db"


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    # Resolve db location and create parent directory on first run.
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


def init_db(db_path: str | Path | None = None) -> None:
    # Create the scan history table if it does not already exist.
    with _connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                risk_score REAL NOT NULL,
                label TEXT NOT NULL,
                explanation TEXT NOT NULL,
                matched_keywords TEXT NOT NULL,
                ai_tips TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

        # Backfill schema for databases created before ai_tips existed.
        cursor = conn.execute("PRAGMA table_info(scan_history)")
        column_names = {str(row[1]) for row in cursor.fetchall()}
        if "ai_tips" not in column_names:
            conn.execute("ALTER TABLE scan_history ADD COLUMN ai_tips TEXT")

        # Feature 1: Scam Network Visualization Data
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scam_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT,
                receiver_id TEXT,
                message_text TEXT NOT NULL,
                link TEXT,
                scam_score REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)

        # Feature 2: Auto-Block Scam Accounts Data
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_risk (
                user_id TEXT PRIMARY KEY,
                scam_count INTEGER DEFAULT 0,
                risk_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active'
            )
            """)

        conn.commit()


def insert_scan(
    input_text: str,
    risk_score: float,
    label: str,
    explanation: str,
    matched_keywords: list[str],
    ai_tips: str | None = None,
    db_path: str | Path | None = None,
) -> None:
    # Store matched keywords as JSON text for simple SQLite persistence.
    payload = json.dumps(matched_keywords)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO scan_history (
                input_text,
                risk_score,
                label,
                explanation,
                matched_keywords,
                ai_tips
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (input_text, risk_score, label, explanation, payload, ai_tips),
        )
        conn.commit()


def fetch_random_history(
    limit: int = 5, db_path: str | Path | None = None
) -> list[str]:
    # Fetch random previously analyzed inputs for suggestions
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT input_text
            FROM scan_history
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

    return [row[0] for row in rows]


def fetch_history(
    limit: int = 200, db_path: str | Path | None = None
) -> list[dict[str, Any]]:
    # Return newest scans first so recent analysis appears at the top in UI.
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT
                id,
                input_text,
                risk_score,
                label,
                explanation,
                matched_keywords,
                ai_tips,
                created_at
            FROM scan_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "input_text": row[1],
            "risk_score": row[2],
            "label": row[3],
            "explanation": row[4],
            "matched_keywords": json.loads(row[5] or "[]"),
            "ai_tips": row[6],
            "created_at": row[7],
        }
        for row in rows
    ]


def fetch_stats(db_path: str | Path | None = None) -> dict[str, Any]:
    # Aggregate key counts for dashboard cards.
    with _connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN label = 'scam' THEN 1 ELSE 0 END) AS scam_count,
                SUM(CASE WHEN label = 'suspicious' THEN 1 ELSE 0 END) AS suspicious_count,
                SUM(CASE WHEN label = 'safe' THEN 1 ELSE 0 END) AS safe_count
            FROM scan_history
            """)
        total, scam_count, suspicious_count, safe_count = cursor.fetchone()
        total = total or 0
        scam_count = scam_count or 0
        suspicious_count = suspicious_count or 0
        safe_count = safe_count or 0

    scam_rate = round((scam_count / total) * 100.0, 2) if total else 0.0

    # Build a frequency map from recent keyword matches using SQLite json_each
    # for significantly better performance than fetching and parsing in Python.
    with _connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT value, COUNT(*) as count
            FROM (
                SELECT matched_keywords
                FROM scan_history
                ORDER BY id DESC
                LIMIT 1000
            ), json_each(matched_keywords)
            GROUP BY value
            ORDER BY count DESC
            LIMIT 10
        """)
        top_keywords = cursor.fetchall()

    return {
        "total_scans": total,
        "scam_count": scam_count,
        "suspicious_count": suspicious_count,
        "safe_count": safe_count,
        "scam_rate": scam_rate,
        "top_keywords": top_keywords,
    }
