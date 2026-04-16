import sqlite3
from pathlib import Path
from typing import Any

from database.db import DEFAULT_DB_PATH, _connect


def process_scam_event(
    user_id: str, scam_probability: float, db_path: str | Path | None = None
) -> dict[str, Any]:
    """
    Updates the user's risk profile based on a new message and auto-blocks if needed.
    """
    return process_scam_events_batch(
        [{"sender_id": user_id, "scam_score": scam_probability}], db_path
    )[0]


def process_scam_events_batch(
    events: list[dict[str, Any]], db_path: str | Path | None = None
) -> list[dict[str, Any]]:
    """
    Updates the user's risk profile for multiple events in a single transaction.
    """
    if not events:
        return []

    user_updates: dict[str, list[float]] = {}
    for event in events:
        u_id = event["sender_id"]
        score = event["scam_score"]
        if u_id not in user_updates:
            user_updates[u_id] = []
        user_updates[u_id].append(score)

    results = []
    with _connect(db_path) as conn:
        user_ids = list(user_updates.keys())
        # SQLite has a limit on the number of host parameters, but for mock data generation it's usually fine.
        # For very large batches, we might need to chunk this.
        placeholders = ",".join(["?"] * len(user_ids))
        cursor = conn.execute(
            f"SELECT user_id, scam_count, risk_score, status FROM user_risk WHERE user_id IN ({placeholders})",
            user_ids,
        )
        current_states = {
            row[0]: {"scam_count": row[1], "risk_score": row[2], "status": row[3]}
            for row in cursor.fetchall()
        }

        for user_id, scores in user_updates.items():
            if user_id in current_states:
                state = current_states[user_id]
            else:
                state = {"scam_count": 0, "risk_score": 0.0, "status": "active"}
                conn.execute(
                    "INSERT INTO user_risk (user_id, scam_count, risk_score, status) VALUES (?, 0, 0.0, 'active')",
                    (user_id,),
                )

            if state["status"] == "blocked":
                results.append(
                    {"user_id": user_id, "status": "blocked", "action": "none"}
                )
                continue

            new_scam_count = state["scam_count"]
            new_risk_score = state["risk_score"]
            new_status = state["status"]

            for score in scores:
                new_scam_count += 1
                new_risk_score += score
                if new_scam_count >= 3 and new_risk_score >= 2.0:
                    new_status = "blocked"
                    break

            action = "updated" if new_status == "active" else "blocked"

            conn.execute(
                """
                UPDATE user_risk
                SET scam_count = ?, risk_score = ?, status = ?
                WHERE user_id = ?
                """,
                (new_scam_count, new_risk_score, new_status, user_id),
            )

            results.append(
                {
                    "user_id": user_id,
                    "scam_count": new_scam_count,
                    "risk_score": round(new_risk_score, 2),
                    "status": new_status,
                    "action": action,
                }
            )
        conn.commit()

    return results


def get_blocked_users(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Returns a list of blocked users."""
    with _connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT user_id, scam_count, risk_score, status
            FROM user_risk
            WHERE status = 'blocked'
            ORDER BY risk_score DESC
            """)
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
            (user_id,),
        )
        conn.commit()


def get_top_dangerous_accounts(
    limit: int = 10, db_path: str | Path | None = None
) -> list[dict[str, Any]]:
    """Returns the top most dangerous accounts."""
    with _connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT user_id, scam_count, risk_score, status
            FROM user_risk
            ORDER BY risk_score DESC
            LIMIT ?
            """,
            (limit,),
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
