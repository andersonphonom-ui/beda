import random


# ═══════════════════════════════════════════════════════════════
#  USER AGENTS DATABASE
# ═══════════════════════════════════════════════════════════════

USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Firefox Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    # Android Chrome
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Samsung Galaxy S23) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "fr-FR,fr;q=0.9,en;q=0.8",
    "de-DE,de;q=0.9,en;q=0.8",
    "ar-SA,ar;q=0.9,en;q=0.8",
    "es-ES,es;q=0.9,en;q=0.8",
    "it-IT,it;q=0.9,en;q=0.8",
    "pt-BR,pt;q=0.9,en;q=0.8",
    "ja-JP,ja;q=0.9,en;q=0.8",
    "zh-CN,zh;q=0.9,en;q=0.8",
]

ACCEPT_ENCODINGS = [
    "gzip, deflate, br",
    "gzip, deflate",
    "br, gzip, deflate",
]

PLATFORMS = [
    '"Windows"',
    '"macOS"',
    '"Linux"',
    '"iPhone"',
    '"Android"',
]

SEC_CH_UA_LIST = [
    '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    '"Chromium";v="123", "Google Chrome";v="123", "Not-A.Brand";v="99"',
    '"Microsoft Edge";v="124", "Chromium";v="124", "Not-A.Brand";v="99"',
    '"Firefox";v="125", "Not-A.Brand";v="99"',
]


# ═══════════════════════════════════════════════════════════════
#  FINGERPRINT GENERATOR
# ═══════════════════════════════════════════════════════════════

def get_random_fingerprint():
    """
    Returns a complete set of headers that mimic a real browser.
    Every call returns a different fingerprint.
    """
    ua = random.choice(USER_AGENTS)

    # Detect browser type from UA
    is_mobile  = "Mobile" in ua or "iPhone" in ua or "Android" in ua
    is_chrome  = "Chrome" in ua and "Edg" not in ua
    is_firefox = "Firefox" in ua
    is_safari  = "Safari" in ua and "Chrome" not in ua
    is_edge    = "Edg" in ua

    headers = {
        "User-Agent":       ua,
        "Accept-Language":  random.choice(ACCEPT_LANGUAGES),
        "Accept-Encoding":  random.choice(ACCEPT_ENCODINGS),
        "Connection":       "keep-alive",
        "DNT":              random.choice(["1", "0"]),
        "Upgrade-Insecure-Requests": "1",
    }

    # Chrome/Edge specific headers
    if is_chrome or is_edge:
        headers["sec-ch-ua"]          = random.choice(SEC_CH_UA_LIST)
        headers["sec-ch-ua-mobile"]   = "?1" if is_mobile else "?0"
        headers["sec-ch-ua-platform"] = random.choice(PLATFORMS)
        headers["Sec-Fetch-Site"]     = "same-origin"
        headers["Sec-Fetch-Mode"]     = "navigate"
        headers["Sec-Fetch-User"]     = "?1"
        headers["Sec-Fetch-Dest"]     = "document"

    # Accept header based on browser
    if is_firefox:
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    elif is_safari:
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    else:
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"

    return headers


def get_random_ua():
    """Returns just a random User-Agent string"""
    return random.choice(USER_AGENTS)
