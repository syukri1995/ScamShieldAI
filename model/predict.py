from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from model.rules import apply_rules

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "model.pkl"
VECTORIZER_PATH = MODEL_DIR / "vectorizer.pkl"

_MODEL_CACHE = None
_VECTORIZER_CACHE = None


def _load_artifacts():
    global _MODEL_CACHE, _VECTORIZER_CACHE

    # Return cached instances if already loaded
    if _MODEL_CACHE is not None and _VECTORIZER_CACHE is not None:
        return _MODEL_CACHE, _VECTORIZER_CACHE

    # Load persisted model assets if training has been completed.
    if MODEL_PATH.exists() and VECTORIZER_PATH.exists():
        model = joblib.load(MODEL_PATH)
        vectorizer = joblib.load(VECTORIZER_PATH)
        _MODEL_CACHE = model
        _VECTORIZER_CACHE = vectorizer
        return model, vectorizer
    return None, None


def _heuristic_probability(text: str) -> float:
    # Fallback scoring if model artifacts are not available yet.
    signals = ["urgent", "verify", "winner", "click", "password", "bank", "gift card"]
    lowered = text.lower()
    score = sum(1 for s in signals if s in lowered)
    return min(0.03 + score * 0.08, 0.55)


def _model_explanation(
    vectorizer: Any, model: Any, text: str, top_k: int = 5
) -> list[str]:
    # Rank present terms by positive model weight contribution.
    vec = vectorizer.transform([text])
    feature_names = vectorizer.get_feature_names_out().tolist()
    coef = model.coef_[0]
    present_indices = vec.nonzero()[1]
    if len(present_indices) == 0:
        return []

    weighted = [(idx, coef[idx] * vec[0, idx]) for idx in present_indices]
    ranked = sorted(weighted, key=lambda x: x[1], reverse=True)[:top_k]
    return [feature_names[idx] for idx, _ in ranked if coef[idx] > 0]


def predict_text(text: str) -> dict[str, Any]:
    # Prefer ML inference and fall back to heuristics if artifacts are missing.
    model, vectorizer = _load_artifacts()

    if model is not None and vectorizer is not None:
        vec = vectorizer.transform([text])
        model_prob = float(model.predict_proba(vec)[0][1])
        model_terms = _model_explanation(vectorizer, model, text)
    else:
        model_prob = _heuristic_probability(text)
        model_terms = []

    model_score = model_prob * 100.0
    # Blend with deterministic rules, but keep the trained model as the primary signal.
    rules = apply_rules(text)
    if model is not None and vectorizer is not None:
        # Model-first scoring: rules are assistive only.
        final_score = max(0.0, min(100.0, model_score + (rules["score_boost"] * 0.35)))
    else:
        # Heuristic fallback should stay conservative when model artifacts are missing.
        fallback_boost = min(rules["score_boost"] * 0.2, 8.0)
        final_score = max(0.0, min(100.0, model_score + fallback_boost))

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
        reasons.append(
            "No strong scam indicators were detected by the current model and rules."
        )

    merged_keywords = sorted(set(model_terms + rules["matched_keywords"]))

    # Return UI-ready payload with normalized score and explanation.
    return {
        "risk_score": round(final_score, 2),
        "label": label,
        "model_probability": round(model_prob * 100.0, 2),
        "explanation": " | ".join(reasons),
        "matched_keywords": merged_keywords,
    }
