import sqlite3
from pathlib import Path
from typing import Any

from database.db import _connect, DEFAULT_DB_PATH

def process_scam_event(user_id: str, scam_probability: float, db_path: str | Path | None = None) -> dict[str, Any]:
    """
    Updates the user's risk profile based on a new message and auto-blocks if needed.
    """
    with _connect(db_path) as conn:
        cursor = conn.execute("SELECT scam_count, risk_score, status FROM user_risk WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            scam_count, risk_score, status = row
        else:
            scam_count, risk_score, status = 0, 0.0, "active"
            conn.execute(
                "INSERT INTO user_risk (user_id, scam_count, risk_score, status) VALUES (?, ?, ?, ?)",
                (user_id, scam_count, risk_score, status)
            )

        if status == "blocked":
            # Already blocked, do not process further
            return {"user_id": user_id, "status": "blocked", "action": "none"}

        # Update counts and score
        new_scam_count = scam_count + 1

        # Simple moving average / accumulation for risk score
        # risk_score = (scam_count * average_scam_probability)
        # We can calculate the new average:
        # old_total_prob = old_scam_count * old_average
        # new_total_prob = old_total_prob + scam_probability
        # new_average = new_total_prob / new_scam_count
        # new_risk_score = new_scam_count * new_average = new_total_prob
        new_risk_score = risk_score + scam_probability

        new_status = "active"
        action = "updated"

        # Blocking rule:
        # if scam_count >= 3 and risk_score >= 2.0: status = "blocked"
        if new_scam_count >= 3 and new_risk_score >= 2.0:
            new_status = "blocked"
            action = "blocked"

        conn.execute(
            """
            UPDATE user_risk
            SET scam_count = ?, risk_score = ?, status = ?
            WHERE user_id = ?
            """,
            (new_scam_count, new_risk_score, new_status, user_id)
        )
        conn.commit()

    return {
        "user_id": user_id,
        "scam_count": new_scam_count,
        "risk_score": round(new_risk_score, 2),
        "status": new_status,
        "action": action
    }

def get_blocked_users(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Returns a list of blocked users."""
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT user_id, scam_count, risk_score, status
            FROM user_risk
            WHERE status = 'blocked'
            ORDER BY risk_score DESC
            """
        )
        rows = cursor.fetchall()

    return [
        {
            "user_id": row[0],
            "scam_count": row[1],
            "risk_score": round(row[2], 2),
            "status": row[3],
        }
        for row in rows
    ]

def unblock_user(user_id: str, db_path: str | Path | None = None) -> None:
    """Unblocks a user and resets their risk score."""
    with _connect(db_path) as conn:
        conn.execute(
            """
            UPDATE user_risk
            SET status = 'active', scam_count = 0, risk_score = 0.0
            WHERE user_id = ?
            """,
            (user_id,)
        )
        conn.commit()

def get_top_dangerous_accounts(limit: int = 10, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Returns the top most dangerous accounts."""
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT user_id, scam_count, risk_score, status
            FROM user_risk
            ORDER BY risk_score DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()

    return [
        {
            "user_id": row[0],
            "scam_count": row[1],
            "risk_score": round(row[2], 2),
            "status": row[3],
        }
        for row in rows
    ]
