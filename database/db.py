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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """)
        conn.commit()


def insert_scan(
    input_text: str,
    risk_score: float,
    label: str,
    explanation: str,
    matched_keywords: list[str],
    db_path: str | Path | None = None,
) -> None:
    # Store matched keywords as JSON text for simple SQLite persistence.
    payload = json.dumps(matched_keywords)
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO scan_history (input_text, risk_score, label, explanation, matched_keywords)
            VALUES (?, ?, ?, ?, ?)
            """,
            (input_text, risk_score, label, explanation, payload),
        )
        conn.commit()


def fetch_history(
    limit: int = 200, db_path: str | Path | None = None
) -> list[dict[str, Any]]:
    # Return newest scans first so recent analysis appears at the top in UI.
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT id, input_text, risk_score, label, explanation, matched_keywords, created_at
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
            "created_at": row[6],
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

    # Build a frequency map from recent keyword matches.
    keyword_counts: dict[str, int] = {}
    for item in fetch_history(limit=1000, db_path=db_path):
        for kw in item["matched_keywords"]:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1

    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_scans": total,
        "scam_count": scam_count,
        "suspicious_count": suspicious_count,
        "safe_count": safe_count,
        "scam_rate": scam_rate,
        "top_keywords": top_keywords,
    }
