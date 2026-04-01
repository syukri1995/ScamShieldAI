from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np

from model.rules import apply_rules

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "model.pkl"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.pkl"


def _load_artifacts():
    if MODEL_PATH.exists() and VECTORIZER_PATH.exists():
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        return model, vectorizer
    return None, None


def _heuristic_probability(text: str) -> float:
    # Fallback scoring if model artifacts are not available yet.
    signals = ["urgent", "verify", "winner", "click", "password", "bank", "gift card"]
    lowered = text.lower()
    score = sum(1 for s in signals if s in lowered)
    return min(0.1 + score * 0.15, 0.95)


def _model_explanation(vectorizer: Any, model: Any, text: str, top_k: int = 5) -> list[str]:
    vec = vectorizer.transform([text])
    feature_names = np.array(vectorizer.get_feature_names_out())
    coef = model.coef_[0]
    present_indices = vec.nonzero()[1]
    if len(present_indices) == 0:
        return []

    weighted = [(idx, coef[idx] * vec[0, idx]) for idx in present_indices]
    ranked = sorted(weighted, key=lambda x: x[1], reverse=True)[:top_k]
    return [feature_names[idx] for idx, _ in ranked if coef[idx] > 0]


def predict_text(text: str) -> dict[str, Any]:
    model, vectorizer = _load_artifacts()

    if model is not None and vectorizer is not None:
        vec = vectorizer.transform([text])
        model_prob = float(model.predict_proba(vec)[0][1])
        model_terms = _model_explanation(vectorizer, model, text)
    else:
        model_prob = _heuristic_probability(text)
        model_terms = []

    model_score = model_prob * 100.0
    rules = apply_rules(text)
    final_score = max(0.0, min(100.0, model_score + rules["score_boost"]))

    if final_score >= 70:
        label = "scam"
    elif final_score >= 40:
        label = "suspicious"
    else:
        label = "safe"

    reasons = []
    if model_terms:
        reasons.append(f"Model-highlighted terms: {', '.join(model_terms)}")
    reasons.extend(rules["rule_reasons"])

    if not reasons:
        reasons.append("No strong scam indicators were detected by the current model and rules.")

    merged_keywords = sorted(set(model_terms + rules["matched_keywords"]))

    return {
        "risk_score": round(final_score, 2),
        "label": label,
        "model_probability": round(model_prob * 100.0, 2),
        "explanation": " | ".join(reasons),
        "matched_keywords": merged_keywords,
    }
