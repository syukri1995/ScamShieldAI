import re

SUSPICIOUS_KEYWORDS = {
    "urgent",
    "verify",
    "account",
    "suspended",
    "winner",
    "prize",
    "lottery",
    "claim",
    "click",
    "password",
    "otp",
    "bank",
    "refund",
    "gift card",
    "wire transfer",
    "limited time",
}

URL_SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "rb.gy")
SUSPICIOUS_TLDS = (".xyz", ".top", ".work", ".click", ".info")

# Pre-compiled regex patterns for performance
URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")
IP_URL_PATTERN = re.compile(r"https?://\d+\.\d+\.\d+\.\d+")


def detect_urls(text: str) -> list[str]:
    # Capture common URL formats found in message text.
    return URL_PATTERN.findall(text.lower())


def apply_rules(text: str) -> dict:
    # Collect keyword and URL based warning signals.
    lowered = text.lower()
    matched_keywords = sorted([kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered])

    url_flags = set()
    for url in detect_urls(text):
        if any(shortener in url for shortener in URL_SHORTENERS):
            url_flags.add("uses_url_shortener")
        if IP_URL_PATTERN.search(url):
            url_flags.add("ip_based_url")
        if any(url.endswith(tld) for tld in SUSPICIOUS_TLDS):
            url_flags.add("suspicious_tld")

    boost = 0.0
    # Cap each signal family so scores stay bounded and interpretable.
    boost += min(len(matched_keywords) * 6.0, 30.0)
    boost += min(len(url_flags) * 9.0, 27.0)

    reasons = []
    if matched_keywords:
        reasons.append(
            f"Suspicious keywords detected: {', '.join(matched_keywords[:6])}"
        )
    if url_flags:
        reasons.append(f"URL warning signals: {', '.join(sorted(url_flags))}")

    # Return additive boost, matched terms, and human-readable reasons.
    return {
        "score_boost": boost,
        "matched_keywords": matched_keywords,
        "url_flags": sorted(url_flags),
        "rule_reasons": reasons,
    }
