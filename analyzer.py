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

        # ── Find the LOGIN form specifically (the one with a password field) ──
        all_forms = soup.find_all("form")
        form = None
        for f in all_forms:
            if f.find("input", {"type": "password"}):
                form = f
                break
        if not form and all_forms:
            form = all_forms[0]  # fallback: first form (e.g. multi-step email-only form)

        if form and form.get("action"):
            action = form.get("action")
            if action.startswith("http"):
                result["action_url"] = action
            elif action.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                result["action_url"] = f"{parsed.scheme}://{parsed.netloc}{action}"
            else:
                # Relative action without leading slash (e.g. "doLogin")
                from urllib.parse import urlparse
                parsed = urlparse(url)
                base_path = parsed.path.rsplit("/", 1)[0]
                result["action_url"] = f"{parsed.scheme}://{parsed.netloc}{base_path}/{action}"

        # ── Find all inputs (scoped to the login form only, if found) ──
        inputs = form.find_all("input") if form else soup.find_all("input")

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
    Requires explicit, reliable signals — avoids false positives from
    minor page differences (timestamps, tokens, session IDs, etc).
    """
    # Explicit success text — most reliable, user-provided
    if success_text and success_text.lower() in response.text.lower():
        return True

    # Explicit fail text disappeared — reliable, user-provided
    if fail_text:
        return fail_text.lower() not in response.text.lower()

    # Redirect to a clearly authenticated area — reliable
    if response.url and any(p in response.url.lower() for p in
                             ["/dashboard", "/home", "/panel", "/account/overview", "/welcome", "/feed"]):
        return True

    # Status 302 redirect
    if response.history and response.history[-1].status_code in [301, 302]:
        return True

    # Last resort: compare full response length to baseline (fragile,
    # but far more reliable than matching a 300-char text slice).
    # Only trust this if the difference is substantial (>15%).
    if baseline_text is not None:
        baseline_len  = len(baseline_text)
        response_len  = len(response.text)
        if baseline_len > 0:
            diff_ratio = abs(response_len - baseline_len) / baseline_len
            if diff_ratio > 0.15:
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


def detect_rate_limit(response):
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
        ("captcha is required",      "Captcha detected"),
        ("please complete the captcha", "Captcha detected"),
        ("recaptcha",                 "reCAPTCHA detected"),
        ("are you a robot",           "Bot detection triggered"),
        ("your ip has been blocked",  "IP blocked by server"),
        ("your ip address has been blocked", "IP blocked by server"),
        ("too many requests",         "Too many requests"),
        ("rate limit exceeded",       "Rate limit hit"),
        ("access denied",             "Access denied"),
        ("suspicious activity detected", "Suspicious activity detected"),
        ("temporarily blocked",       "Temporarily blocked"),
        ("your ip has been banned",   "IP banned"),
        ("account temporarily locked", "Account locked"),
    ]
    for keyword, message in triggers:
        if keyword in body:
            return message

    # Response too small — possible block page
    if len(response.content) < 100 and response.status_code not in [200, 302]:
        return f"Suspicious small response ({len(response.content)} bytes)"

    return None
