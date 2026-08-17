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


def detect_multistep(soup):
    """
    Detects if login form is multi-step (email first, then password).
    Returns True if only email/username field visible, no password field.
    """
    inputs = soup.find_all("input")
    has_user = False
    has_pass = False

    for inp in inputs:
        itype = inp.get("type", "").lower()
        name  = inp.get("name", "").lower()

        if itype in ["text", "email"] or any(f in name for f in COMMON_USER_FIELDS):
            has_user = True
        if itype == "password" or any(f in name for f in COMMON_PASS_FIELDS):
            has_pass = True

    # Multi-step: has username but NO password field
    return has_user and not has_pass


def analyze_multistep(url, session, username, timeout=5):
    """
    Handles multi-step login (like Google/Microsoft).
    Step 1: Submit email → get to password page
    Step 2: Return form info for password page
    """
    try:
        # Step 1 — Get email page
        response = session.get(url, timeout=timeout, verify=False)
        soup = BeautifulSoup(response.text, "html.parser")

        if not detect_multistep(soup):
            return None  # Not multi-step

        console.print("  [yellow][BEDA] Multi-step login detected — submitting username first...[/yellow]")

        # Find form
        form = soup.find("form")
        action = url
        if form and form.get("action"):
            act = form.get("action")
            if act.startswith("http"):
                action = act
            elif act.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                action = f"{parsed.scheme}://{parsed.netloc}{act}"

        # Find fields
        inputs  = soup.find_all("input")
        data    = {}
        user_field = None

        for inp in inputs:
            name  = inp.get("name", "")
            itype = inp.get("type", "").lower()
            value = inp.get("value", "")

            if not name:
                continue

            # Hidden fields (CSRF etc.)
            if itype == "hidden":
                data[name] = value

            # Username field
            if itype in ["text", "email"] or any(f in name.lower() for f in COMMON_USER_FIELDS):
                user_field = name
                data[name] = username

        if not user_field:
            return None

        # Step 1 — Submit username
        step1 = session.post(action, data=data, timeout=timeout, verify=False, allow_redirects=True)
        soup2 = BeautifulSoup(step1.text, "html.parser")

        console.print("  [green][BEDA] Username submitted ✅ — now on password page[/green]")

        # Analyze password page
        result = analyze_form(step1.url, session, timeout=timeout)
        if result:
            result["multistep"] = True
            result["step1_url"] = action
            result["step1_data"] = data
        return result

    except Exception as e:
        console.print(f"  [red][BEDA] Multi-step error: {e}[/red]")
        return None
    """Detects if IP is being rate limited or blocked"""

    # Status codes
    if response.status_code == 429:
        return "Rate limit (429 Too Many Requests)"
    if response.status_code == 403:
        return "Forbidden (403) — possible IP block"
    if response.status_code == 503:
        return "Service unavailable (503) — possible DDoS protection"

    # Cloudflare detection
    if "cf-ray" in response.headers or response.status_code == 503:
        return "Cloudflare protection detected"
    if "__cf_bm" in response.cookies:
        return "Cloudflare bot detection triggered"

    # Body keywords
    body = response.text.lower()
    triggers = [
        ("captcha",        "Captcha detected"),
        ("recaptcha",      "reCAPTCHA detected"),
        ("robot",          "Bot detection triggered"),
        ("blocked",        "IP blocked by server"),
        ("too many",       "Too many requests"),
        ("rate limit",     "Rate limit hit"),
        ("access denied",  "Access denied"),
        ("suspicious",     "Suspicious activity detected"),
        ("temporarily",    "Temporarily blocked"),
        ("ban",            "IP banned"),
    ]
    for keyword, message in triggers:
        if keyword in body:
            return message

    # Response too small — possible block page
    if len(response.content) < 100 and response.status_code not in [200, 302]:
        return f"Suspicious small response ({len(response.content)} bytes)"

    return None
