import json
import random
import sqlite3
from pathlib import Path

from database.db import _connect, init_db
from services.risk_engine import process_scam_events_batch


def generate_mock_data():
    init_db()

    events = [
        # === SCAMMER 1: pkg_shipping_fraud (Package Delivery Scams) ===
        {
            "sender_id": "pkg_shipping_fraud",
            "receiver_id": "victim_sarah",
            "message_text": "Your package delivery failed! Update payment here: https://ups-confirm-payment.ru/verify?id=9283",
            "link": "https://ups-confirm-payment.ru/verify?id=9283",
            "scam_score": 0.97,
        },
        {
            "sender_id": "pkg_shipping_fraud",
            "receiver_id": "victim_mike",
            "message_text": "FedEx: Click to reschedule delivery - https://fedex-delivery-app.tk/track",
            "link": "https://fedex-delivery-app.tk/track",
            "scam_score": 0.96,
        },
        {
            "sender_id": "pkg_shipping_fraud",
            "receiver_id": "victim_jessica",
            "message_text": "Your Amazon order needs attention! Confirm address: http://amazon-security-check.com/verify",
            "link": "http://amazon-security-check.com/verify",
            "scam_score": 0.95,
        },
        
        # === SCAMMER 2: bank_phish_kingpin (Banking & Finance Phishing) ===
        {
            "sender_id": "bank_phish_kingpin",
            "receiver_id": "victim_david",
            "message_text": "⚠️URGENT: Your Wells Fargo account was compromised. Verify identity NOW: https://wellsfargo-secure-verifn.com/login",
            "link": "https://wellsfargo-secure-verifn.com/login",
            "scam_score": 0.98,
        },
        {
            "sender_id": "bank_phish_kingpin",
            "receiver_id": "victim_emma",
            "message_text": "Chase Bank: Suspicious activity detected. Re-enter credentials: https://chase-online-signon.net/auth",
            "link": "https://chase-online-signon.net/auth",
            "scam_score": 0.97,
        },
        {
            "sender_id": "bank_phish_kingpin",
            "receiver_id": "victim_marcus",
            "message_text": "PayPal security alert. Confirm your payment method: https://paypa1-confirm-method.ru",
            "link": "https://paypa1-confirm-method.ru",
            "scam_score": 0.96,
        },
        
        # === SCAMMER 3: romance_scammer_nova (Romance/Catfish) ===
        {
            "sender_id": "romance_scammer_nova",
            "receiver_id": "victim_linda",
            "message_text": "Hi beautiful! I'm so into you. I need help with an emergency. Can you wire $500 to this account? Bank details: https://money-transfer.io/send?to=ng_account_3487",
            "link": "https://money-transfer.io/send?to=ng_account_3487",
            "scam_score": 0.94,
        },
        {
            "sender_id": "romance_scammer_nova",
            "receiver_id": "victim_robert",
            "message_text": "Been thinking about you... I need $2000 for my surgery. Can you help? Western Union to: https://wu-transfer-service.tk/send",
            "link": "https://wu-transfer-service.tk/send",
            "scam_score": 0.93,
        },
        
        # === SCAMMER 4: crypto_pump_dump (Cryptocurrency Pump & Dump) ===
        {
            "sender_id": "crypto_pump_dump",
            "receiver_id": "victim_james",
            "message_text": "🚀 EARLY ACCESS: Our new token launching TONIGHT. 1000x potential! Buy now at exclusive price: https://cryptotoken-presale.io/buy?ref=james",
            "link": "https://cryptotoken-presale.io/buy?ref=james",
            "scam_score": 0.92,
        },
        {
            "sender_id": "crypto_pump_dump",
            "receiver_id": "victim_rachel",
            "message_text": "Limited slots! Earn 200% daily ROI with ElonMax coin. DM me to join the group: https://t.me/elonmax_investors",
            "link": "https://t.me/elonmax_investors",
            "scam_score": 0.91,
        },
        {
            "sender_id": "crypto_pump_dump",
            "receiver_id": "victim_chris",
            "message_text": "Metamask wallet update required immediately! Your funds at risk: https://metamask-security-update.net/sync",
            "link": "https://metamask-security-update.net/sync",
            "scam_score": 0.90,
        },
        
        # === SCAMMER 5: tech_support_scammer (Tech Support / Microsoft Scam) ===
        {
            "sender_id": "tech_support_scammer",
            "receiver_id": "victim_patricia",
            "message_text": "ALERT: Your computer has been infected with malware! Call 1-800-TECH-FIX or visit: https://windows-security-alert.net/scan",
            "link": "https://windows-security-alert.net/scan",
            "scam_score": 0.95,
        },
        {
            "sender_id": "tech_support_scammer",
            "receiver_id": "victim_thomas",
            "message_text": "Microsoft Security Warning: Virus detected on your device. Download removal tool: https://ms-antivirus-fix.ru/download",
            "link": "https://ms-antivirus-fix.ru/download",
            "scam_score": 0.94,
        },
        
        # === SCAMMER 6: job_offer_scammer (Fake Job Offers) ===
        {
            "sender_id": "job_offer_scammer",
            "receiver_id": "victim_kevin",
            "message_text": "$8000/week working from home! No experience needed. Apply here: https://easy-work-from-home.tk/apply?job_id=wfh_2024",
            "link": "https://easy-work-from-home.tk/apply?job_id=wfh_2024",
            "scam_score": 0.89,
        },
        {
            "sender_id": "job_offer_scammer",
            "receiver_id": "victim_angela",
            "message_text": "Google Hiring Team: Your CV was selected! Complete verification here: https://google-recruit.ru/verify-cv",
            "link": "https://google-recruit.ru/verify-cv",
            "scam_score": 0.88,
        },
        
        # === SCAMMER 7: tax_refund_scammer (Tax/Government Impersonation) ===
        {
            "sender_id": "tax_refund_scammer",
            "receiver_id": "victim_paul",
            "message_text": "IRS NOTICE: You have a tax refund of $3,847! Claim it now: https://irs-tax-refund-claim.net/validate?id=paul_2024",
            "link": "https://irs-tax-refund-claim.net/validate?id=paul_2024",
            "scam_score": 0.96,
        },
        {
            "sender_id": "tax_refund_scammer",
            "receiver_id": "victim_susan",
            "message_text": "Social Security: Your account is flagged for fraud. Verify identity: https://ss-verify-account.ru/secure-login",
            "link": "https://ss-verify-account.ru/secure-login",
            "scam_score": 0.95,
        },
        
        # === LEGITIMATE USERS (for contrast) ===
        {
            "sender_id": "friend_john",
            "receiver_id": "victim_sarah",
            "message_text": "Hey! Are we still on for lunch tomorrow at noon?",
            "link": "",
            "scam_score": 0.02,
        },
        {
            "sender_id": "coworker_lisa",
            "receiver_id": "victim_david",
            "message_text": "Can you review the project proposal I sent? Let me know your thoughts.",
            "link": "",
            "scam_score": 0.03,
        },
        {
            "sender_id": "support_team",
            "receiver_id": "victim_emma",
            "message_text": "Your order #12345 has been shipped! Track it at: https://tracking.legit-retailer.com/track?order=12345",
            "link": "https://tracking.legit-retailer.com/track?order=12345",
            "scam_score": 0.08,
        },
    ]

    with _connect() as conn:
        for event in events:
            # Insert into scam_events
            conn.execute(
                """
                INSERT INTO scam_events (sender_id, receiver_id, message_text, link, scam_score)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event["sender_id"],
                    event["receiver_id"],
                    event["message_text"],
                    event["link"],
                    event["scam_score"],
                ),
            )
        conn.commit()

    # Process risk engine (update user_risk and auto-block if necessary)
    # Only process if score is high enough to be considered a scam attempt
    scam_events_to_process = [e for e in events if e["scam_score"] > 0.5]
    if scam_events_to_process:
        process_scam_events_batch(scam_events_to_process)


if __name__ == "__main__":
    generate_mock_data()
    print("Mock data generated successfully.")
