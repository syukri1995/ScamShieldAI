from pathlib import Path

from database.db import fetch_history, fetch_stats, init_db, insert_scan


def test_db_insert_and_fetch(tmp_path: Path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    insert_scan(
        input_text="Urgent verify account",
        risk_score=83.2,
        label="scam",
        explanation="Suspicious keywords detected",
        matched_keywords=["urgent", "verify"],
        db_path=db_path,
    )

    history = fetch_history(db_path=db_path)
    assert len(history) == 1
    assert history[0]["label"] == "scam"


def test_db_stats(tmp_path: Path):
    db_path = tmp_path / "stats.db"
    init_db(db_path)
    insert_scan("safe message", 15.0, "safe", "None", [], db_path)
    insert_scan("bad link", 88.0, "scam", "URL warning", ["click"], db_path)

    stats = fetch_stats(db_path)
    assert stats["total_scans"] == 2
    assert stats["scam_count"] == 1
