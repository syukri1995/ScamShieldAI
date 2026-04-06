from services.analyzer_service import generate_ai_tips


def test_generate_ai_tips_skips_safe_label(monkeypatch):
    # Safe labels should never trigger provider calls.
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    result = generate_ai_tips(
        "Hello team, meeting tomorrow at 10",
        {
            "label": "safe",
            "risk_score": 8,
            "explanation": "No suspicious signal",
            "matched_keywords": [],
        },
    )
    assert result is None


def test_generate_ai_tips_without_api_key_returns_none(monkeypatch):
    # Missing API key should disable tips without error.
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = generate_ai_tips(
        "Urgent verify account",
        {
            "label": "scam",
            "risk_score": 92,
            "explanation": "Phishing indicators detected",
            "matched_keywords": ["urgent", "verify"],
        },
    )
    assert result is None
