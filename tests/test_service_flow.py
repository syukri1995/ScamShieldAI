from pathlib import Path

from database.db import fetch_history, init_db
from services.analyzer_service import analyze_and_store


def test_analyze_and_store(tmp_path: Path):
    db_path = tmp_path / "service.db"
    init_db(db_path)

    result = analyze_and_store("Urgent winner claim your prize now", db_path=db_path)
    assert result["risk_score"] >= 0

    history = fetch_history(db_path=db_path)
    assert len(history) == 1


def test_analyze_rejects_empty(tmp_path: Path):
    db_path = tmp_path / "service2.db"
    init_db(db_path)

    try:
        analyze_and_store("   ", db_path=db_path)
    except ValueError:
        assert True
        return
    assert False
