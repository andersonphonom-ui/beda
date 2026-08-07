import requests
import urllib3
from bs4 import BeautifulSoup
from rich.console import Console

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
console = Console()

COMMON_USER_FIELDS  = ["username", "user", "email", "login", "uname", "usr", "identifier"]
COMMON_PASS_FIELDS  = ["password", "pass", "passwd", "pwd", "secret", "passphrase"]
COMMON_CSRF_FIELDS  = ["csrf", "csrf_token", "_token", "token", "authenticity_token",
                        "_csrf", "csrfmiddlewaretoken", "csrf-token", "nonce"]


def analyze_form(url, session, timeout=5):
    """
    Auto-detects login form fields and CSRF token.
    Returns {user_field, pass_field, csrf_field, csrf_value, action_url}
    """
    try:
        response = session.get(url, timeout=timeout, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        result = {
            "user_field":  None,
            "pass_field":  None,
            "csrf_field":  None,
            "csrf_value":  None,
            "action_url":  url,
        }

        # ── Find form action ──
        form = soup.find("form")
        if form and form.get("action"):
            action = form.get("action")
            if action.startswith("http"):
                result["action_url"] = action
            elif action.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                result["action_url"] = f"{parsed.scheme}://{parsed.netloc}{action}"

        # ── Find all inputs ──
        inputs = soup.find_all("input")

        for inp in inputs:
            name  = inp.get("name", "").lower()
            itype = inp.get("type", "").lower()
            value = inp.get("value", "")

            # CSRF detection
            for csrf in COMMON_CSRF_FIELDS:
                if csrf in name:
                    result["csrf_field"] = inp.get("name")
                    result["csrf_value"] = value
                    break

            # Username field detection
            if not result["user_field"]:
                if itype in ["text", "email"] or name in COMMON_USER_FIELDS:
                    for field in COMMON_USER_FIELDS:
                        if field in name:
                            result["user_field"] = inp.get("name")
                            break

            # Password field detection
            if not result["pass_field"]:
                if itype == "password" or name in COMMON_PASS_FIELDS:
                    result["pass_field"] = inp.get("name")

        return result

    except Exception as e:
        console.print(f"[red]❌ Form analysis failed: {e}[/red]")
        return None


def detect_success(response, baseline_text, success_text=None, fail_text=None):
    """
    Detects if login was successful.
    """
    # Explicit success text
    if success_text and success_text.lower() in response.text.lower():
        return True

    # Explicit fail text disappeared
    if fail_text and fail_text.lower() not in response.text.lower():
        return True

    # Baseline comparison
    if baseline_text and baseline_text.lower() not in response.text.lower():
        return True

    # Redirect to dashboard/home
    if response.url and any(p in response.url for p in ["/dashboard", "/home", "/panel", "/account", "/profile"]):
        return True

    # Status 302 redirect
    if response.history and response.history[-1].status_code in [301, 302]:
        return True

    return False


def detect_rate_limit(response):
    """Detects if IP is being rate limited or blocked"""
    if response.status_code == 429:
        return "Rate limit (429)"
    if response.status_code == 403:
        return "Forbidden (403) — possible IP block"
    body = response.text.lower()
    if any(w in body for w in ["captcha", "robot", "blocked", "too many", "rate limit"]):
        return "Captcha/block detected in response"
    return None
