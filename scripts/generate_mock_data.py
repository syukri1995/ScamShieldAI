import json
import sqlite3
import random
from pathlib import Path

from database.db import init_db, _connect
from services.risk_engine import process_scam_event

def generate_mock_data():
    init_db()

    events = [
        {"sender_id": "scammer_99", "receiver_id": "victim_alice", "message_text": "Win a free gift card! Click here http://fake-gift.com", "link": "http://fake-gift.com", "scam_score": 0.95},
        {"sender_id": "scammer_99", "receiver_id": "victim_bob", "message_text": "Win a free gift card! Click here http://fake-gift.com", "link": "http://fake-gift.com", "scam_score": 0.92},
        {"sender_id": "scammer_99", "receiver_id": "victim_charlie", "message_text": "Win a free gift card! Click here http://fake-gift.com", "link": "http://fake-gift.com", "scam_score": 0.94},
        {"sender_id": "crypto_bro", "receiver_id": "victim_dave", "message_text": "Invest in my new coin! https://crypto-scam.io", "link": "https://crypto-scam.io", "scam_score": 0.88},
        {"sender_id": "crypto_bro", "receiver_id": "victim_eve", "message_text": "1000% returns guaranteed! https://crypto-scam.io", "link": "https://crypto-scam.io", "scam_score": 0.89},
        {"sender_id": "scammer_42", "receiver_id": "victim_frank", "message_text": "Your account is locked. Verify here: http://bank-verify-now.com", "link": "http://bank-verify-now.com", "scam_score": 0.99},
        {"sender_id": "scammer_42", "receiver_id": "victim_grace", "message_text": "Your account is locked. Verify here: http://bank-verify-now.com", "link": "http://bank-verify-now.com", "scam_score": 0.98},
        {"sender_id": "scammer_42", "receiver_id": "victim_heidi", "message_text": "Your account is locked. Verify here: http://bank-verify-now.com", "link": "http://bank-verify-now.com", "scam_score": 0.97},
        {"sender_id": "legit_user", "receiver_id": "victim_alice", "message_text": "Hey, what time are we meeting?", "link": "", "scam_score": 0.05},
        {"sender_id": "legit_user", "receiver_id": "victim_bob", "message_text": "Check out this cool video https://youtube.com/watch?v=123", "link": "https://youtube.com/watch?v=123", "scam_score": 0.12},
    ]

    with _connect() as conn:
        for event in events:
            # Insert into scam_events
            conn.execute(
                """
                INSERT INTO scam_events (sender_id, receiver_id, message_text, link, scam_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event["sender_id"], event["receiver_id"], event["message_text"], event["link"], event["scam_score"])
            )
        conn.commit()

    for event in events:
        # Process risk engine (update user_risk and auto-block if necessary)
        # Only process if score is high enough to be considered a scam attempt
        if event["scam_score"] > 0.5:
            process_scam_event(event["sender_id"], event["scam_score"])

if __name__ == "__main__":
    generate_mock_data()
    print("Mock data generated successfully.")
