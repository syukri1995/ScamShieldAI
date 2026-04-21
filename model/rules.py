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


URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")
IP_PATTERN = re.compile(r"https?://\d+\.\d+\.\d+\.\d+")


def detect_urls(text: str) -> list[str]:
    # Capture common URL formats found in message text.
    return URL_PATTERN.findall(text.lower())


def apply_rules(text: str) -> dict:
    # Collect keyword and URL based warning signals.
    lowered = text.lower()
    matched_keywords = sorted([kw for kw in SUSPICIOUS_KEYWORDS if kw in lowered])

    url_flags = []
    urls = URL_PATTERN.findall(lowered)

    if urls:
        has_shortener = False
        has_ip = False
        has_tld = False

        for url in urls:
            if not has_shortener and any(
                shortener in url for shortener in URL_SHORTENERS
            ):
                has_shortener = True
                url_flags.append("uses_url_shortener")
            if not has_ip and IP_PATTERN.search(url):
                has_ip = True
                url_flags.append("ip_based_url")
            if not has_tld and any(url.endswith(tld) for tld in SUSPICIOUS_TLDS):
                has_tld = True
                url_flags.append("suspicious_tld")

            if len(url_flags) == 3:  # All distinct flags found
                break

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
        # url_flags is already distinct and we append at most 3 elements
        reasons.append(f"URL warning signals: {', '.join(sorted(url_flags))}")

    # Return additive boost, matched terms, and human-readable reasons.
    return {
        "score_boost": boost,
        "matched_keywords": matched_keywords,
        "url_flags": sorted(url_flags),
        "rule_reasons": reasons,
    }
