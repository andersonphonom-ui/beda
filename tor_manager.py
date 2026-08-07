import time
import requests
import subprocess
from rich.console import Console

console = Console()

TOR_SOCKS   = "socks5h://127.0.0.1:9050"
TOR_CONTROL = 9051


def start_tor():
    """Start Tor if not running"""
    try:
        result = subprocess.run(["pgrep", "tor"], capture_output=True)
        if result.returncode != 0:
            subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print("  [cyan][TOR] Starting Tor...[/cyan]")
            time.sleep(5)
        console.print("  [green][TOR] Tor is running ✅[/green]")
        return True
    except Exception as e:
        console.print(f"  [red][TOR] Failed to start Tor: {e}[/red]")
        return False


def get_tor_proxies():
    return {
        "http":  TOR_SOCKS,
        "https": TOR_SOCKS,
    }


def change_ip():
    """Request new Tor identity = new IP"""
    try:
        from stem import Signal
        from stem.control import Controller
        with Controller.from_port(port=TOR_CONTROL) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            time.sleep(3)
            console.print("  [cyan][TOR] IP rotated ✅[/cyan]")
            return True
    except Exception:
        # Fallback: restart tor
        try:
            subprocess.run(["pkill", "tor"])
            time.sleep(1)
            subprocess.Popen(["tor"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(5)
            console.print("  [cyan][TOR] IP rotated (restart) ✅[/cyan]")
            return True
        except Exception as e:
            console.print(f"  [red][TOR] IP rotation failed: {e}[/red]")
            return False


def get_current_ip(proxies=None):
    """Get current public IP"""
    try:
        r = requests.get(
            "https://api.ipify.org",
            proxies=proxies,
            timeout=10
        )
        return r.text.strip()
    except Exception:
        return "Unknown"
