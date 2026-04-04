from pathlib import Path

from database.db import fetch_history, fetch_stats


def get_scan_history(limit: int = 200, db_path: str | Path | None = None):
    # Service wrapper for history retrieval used by the history page.
    return fetch_history(limit=limit, db_path=db_path)


def get_dashboard_stats(db_path: str | Path | None = None):
    # Service wrapper for dashboard aggregates.
    return fetch_stats(db_path=db_path)
