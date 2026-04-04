from model.predict import predict_text


def test_predict_output_shape():
    # Ensure prediction payload contains required keys and valid score bounds.
    result = predict_text("Urgent: verify account now at http://bit.ly/reset")
    assert "risk_score" in result
    assert "label" in result
    assert "explanation" in result
    assert 0 <= result["risk_score"] <= 100


def test_predict_empty_like_safe_signal():
    # Non-obvious safe-ish text should still return a known label category.
    result = predict_text("Hello team, meeting is tomorrow at 10")
    assert result["label"] in {"safe", "suspicious", "scam"}
