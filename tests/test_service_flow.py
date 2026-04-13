from pathlib import Path
from unittest.mock import patch

from database.db import fetch_history, init_db
from services.analyzer_service import analyze_and_store


def test_analyze_and_store(tmp_path: Path):
    # End-to-end check: analyze input and persist exactly one history record.
    db_path = tmp_path / "service.db"
    init_db(db_path)

    result = analyze_and_store(
        "Urgent winner claim your prize now",
        sender_id="test_sender",
        db_path=db_path,
    )
    assert result["risk_score"] >= 0

    history = fetch_history(db_path=db_path)
    assert len(history) == 1


def test_analyze_rejects_empty(tmp_path: Path):
    # Empty input should fail fast with ValueError.
    db_path = tmp_path / "service2.db"
    init_db(db_path)

    try:
        analyze_and_store("   ", db_path=db_path)
    except ValueError:
        assert True
        return
    assert False


@patch(
    "services.analyzer_service.generate_ai_tips",
    return_value="- Block sender\n- Do not click links",
)
def test_analyze_stores_ai_tips(mock_generate, tmp_path: Path):
    # Suspicious/scam analysis should persist generated AI tips.
    db_path = tmp_path / "service_ai.db"
    init_db(db_path)

    result = analyze_and_store(
        "Urgent verify your bank account now",
        sender_id="test_sender",
        db_path=db_path,
    )
    assert result.get("ai_tips")

    history = fetch_history(db_path=db_path)
    assert len(history) == 1
    assert history[0]["ai_tips"] == result["ai_tips"]
    assert mock_generate.call_count == 1


@patch(
    "services.analyzer_service.generate_ai_tips",
    side_effect=RuntimeError("provider down"),
)
def test_analyze_survives_ai_tip_failure(_mock_generate, tmp_path: Path):
    # AI-tip failure must not break normal analysis/persistence.
    db_path = tmp_path / "service_ai_fallback.db"
    init_db(db_path)

    result = analyze_and_store(
        "Claim your winner prize now",
        sender_id="test_sender",
        db_path=db_path,
    )
    assert result.get("ai_tips") is None

    history = fetch_history(db_path=db_path)
    assert len(history) == 1
    assert history[0]["ai_tips"] is None
