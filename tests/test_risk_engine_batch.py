from pathlib import Path
from services.risk_engine import process_scam_event, process_scam_events_batch, get_blocked_users
from database.db import init_db

def test_process_scam_event_single(tmp_path: Path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    res = process_scam_event("user1", 0.9, db_path=db_path)
    assert res["user_id"] == "user1"
    assert res["scam_count"] == 1
    assert res["risk_score"] == 0.9
    assert res["status"] == "active"

def test_process_scam_events_batch(tmp_path: Path):
    db_path = tmp_path / "test_batch.db"
    init_db(db_path)
    events = [
        {"sender_id": "user1", "scam_score": 0.8},
        {"sender_id": "user1", "scam_score": 0.9},
        {"sender_id": "user2", "scam_score": 0.7},
    ]
    results = process_scam_events_batch(events, db_path=db_path)
    assert len(results) == 2

    user1_res = next(r for r in results if r["user_id"] == "user1")
    user2_res = next(r for r in results if r["user_id"] == "user2")

    assert user1_res["scam_count"] == 2
    assert user1_res["risk_score"] == 1.7
    assert user2_res["scam_count"] == 1
    assert user2_res["risk_score"] == 0.7

def test_auto_block(tmp_path: Path):
    db_path = tmp_path / "test_block.db"
    init_db(db_path)
    events = [
        {"sender_id": "scammer", "scam_score": 0.9},
        {"sender_id": "scammer", "scam_score": 0.9},
        {"sender_id": "scammer", "scam_score": 0.9},
    ]
    # First two events
    process_scam_events_batch(events[:2], db_path=db_path)
    blocked = get_blocked_users(db_path=db_path)
    assert len(blocked) == 0

    # Third event
    process_scam_events_batch([events[2]], db_path=db_path)
    blocked = get_blocked_users(db_path=db_path)
    assert len(blocked) == 1
    assert blocked[0]["user_id"] == "scammer"
    assert blocked[0]["status"] == "blocked"

def test_already_blocked(tmp_path: Path):
    db_path = tmp_path / "test_blocked_already.db"
    init_db(db_path)
    # Block user
    events = [{"sender_id": "scammer", "scam_score": 1.0}] * 3
    process_scam_events_batch(events, db_path=db_path)

    # Another event for blocked user
    res = process_scam_event("scammer", 1.0, db_path=db_path)
    assert res["status"] == "blocked"
    assert res["action"] == "none"
