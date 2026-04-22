import re
import os
from importlib import import_module
from pathlib import Path
from typing import Any

from database.db import insert_scan
from model.predict import predict_text

SCAM_LIKE_LABELS = {"suspicious", "scam"}


URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_MODEL_ENV = "OPENAI_MODEL"
OPENAI_TIMEOUT_ENV = "OPENAI_TIMEOUT"
ENV_FILE_CANDIDATES = [
    Path(__file__).resolve().parents[1] / ".env",
    Path(__file__).resolve().parents[1] / "ui" / ".env",
]

_ENV_LOADED = False


def _load_env_files_once() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return

    try:
        dotenv_module = import_module("dotenv")
        load_dotenv = getattr(dotenv_module, "load_dotenv", None)
    except ImportError:
        load_dotenv = None

    if callable(load_dotenv):
        for env_path in ENV_FILE_CANDIDATES:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path, override=False)

    _ENV_LOADED = True


def _get_env_value(name: str, default: str = "") -> str:
    raw_value = (os.getenv(name, default) or default).strip()
    return raw_value.strip('"').strip("'")


def _extract_output_text(response: Any) -> str:
    text = str(getattr(response, "output_text", "") or "").strip()
    if text:
        return text

    # Fallback extraction for SDK response variants where output_text is empty.
    output = getattr(response, "output", None)
    if not output:
        return ""

    chunks: list[str] = []
    for item in output:
        for content in getattr(item, "content", []) or []:
            candidate = str(getattr(content, "text", "") or "").strip()
            if candidate:
                chunks.append(candidate)
    return "\n".join(chunks).strip()


def generate_ai_tips(text: str, prediction: dict[str, Any]) -> str | None:
    _load_env_files_once()

    label = str(prediction.get("label", "")).lower()
    if label not in SCAM_LIKE_LABELS:
        return None

    api_key = _get_env_value(OPENAI_API_KEY_ENV, "")
    if not api_key:
        return None

    try:
        openai_module = import_module("openai")
        openai_client_cls = getattr(openai_module, "OpenAI", None)
    except ImportError:
        openai_client_cls = None

    if openai_client_cls is None:
        return None

    model_name = _get_env_value(OPENAI_MODEL_ENV, "gpt-4o-mini") or "gpt-4o-mini"

    timeout_seconds = 10.0
    timeout_raw = _get_env_value(OPENAI_TIMEOUT_ENV, "10") or "10"
    try:
        timeout_seconds = max(1.0, float(timeout_raw))
    except ValueError:
        timeout_seconds = 10.0

    matched_keywords = prediction.get("matched_keywords") or []
    matched_keywords_text = ", ".join([str(item) for item in matched_keywords[:8]])

    system_prompt = (
        "You are a cybersecurity assistant. Provide concise safety tips for a user who just "
        "received a suspicious message. Keep advice practical and non-legal. "
        "Return 3 short bullet points."
    )

    user_prompt = (
        f"Message text: {text}\n"
        f"Risk label: {prediction.get('label')}\n"
        f"Risk score: {prediction.get('risk_score')}\n"
        f"Model explanation: {prediction.get('explanation')}\n"
        f"Matched keywords: {matched_keywords_text or 'None'}\n"
        "Create immediate next-step safety guidance for this situation."
    )

    try:
        client = openai_client_cls(api_key=api_key, timeout=timeout_seconds)
        response = client.responses.create(
            model=model_name,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        tips = _extract_output_text(response)
        return tips or None
    except Exception:
        # Tips are optional; prediction/storage flow should continue on provider failures.
        return None


def analyze_and_store(
    input_text: str,
    sender_id: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    # Trim user input and reject empty submissions early.
    text = (input_text or "").strip()
    if not text:
        raise ValueError("Input text cannot be empty.")

    # Run prediction and persist the resulting scan record.
    result = predict_text(text)
    try:
        result["ai_tips"] = generate_ai_tips(text, result)
    except Exception:
        # Keep analysis available even if optional tips path fails unexpectedly.
        result["ai_tips"] = None

    insert_scan(
        input_text=text,
        risk_score=result["risk_score"],
        label=result["label"],
        explanation=result["explanation"],
        matched_keywords=result["matched_keywords"],
        ai_tips=result.get("ai_tips"),
        db_path=db_path,
    )

    # Feature 1 & 2 Integration: Store interaction data and process risk.
    # Normally sender_id and receiver_id would come from the messaging context (e.g. Telegram),
    # but here we infer or use defaults since the standard UI only accepts input text.
    # Extract links from the text using a naive heuristic if any exist
    urls = URL_PATTERN.findall(text.lower())
    extracted_link = ",".join(urls) if urls else ""

    try:
        from database.db import _connect

        sender_value = (sender_id or "unknown_sender").strip() or "unknown_sender"

        with _connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO scam_events (sender_id, receiver_id, message_text, link, scam_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    sender_value,
                    "current_user",
                    text,
                    extracted_link,
                    result["risk_score"] / 100.0,
                ),
            )
            conn.commit()

        from services.risk_engine import process_scam_event

        # Auto-block users who repeatedly send scams
        process_scam_event(sender_value, result["risk_score"] / 100.0, db_path=db_path)
    except Exception as e:
        # Silently fail if there's an issue with the new features to avoid breaking the core analyzer
        pass

    return result
