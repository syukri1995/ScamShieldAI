from pathlib import Path
from typing import Any

from database.db import insert_scan
from model.predict import predict_text


def analyze_and_store(
    input_text: str, db_path: str | Path | None = None
) -> dict[str, Any]:
    # Trim user input and reject empty submissions early.
    text = (input_text or "").strip()
    if not text:
        raise ValueError("Input text cannot be empty.")

    # Run prediction and persist the resulting scan record.
    result = predict_text(text)
    insert_scan(
        input_text=text,
        risk_score=result["risk_score"],
        label=result["label"],
        explanation=result["explanation"],
        matched_keywords=result["matched_keywords"],
        db_path=db_path,
    )
    return result
