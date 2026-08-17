import requests
import urllib3
import threading
import time
from rich.console import Console

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
console = Console()

TEST_URL     = "https://api.ipify.org"
TEST_TIMEOUT = 8


# ═══════════════════════════════════════════════════════════════
#  PROXY LOADER
# ═══════════════════════════════════════════════════════════════

def load_proxies(filepath):
    """
    Loads proxies from file.
    Supports formats:
      - http://ip:port
      - socks5://ip:port
      - ip:port (assumed http)
    """
    proxies = []
    try:
        with open(filepath, "r", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if not line.startswith("http") and not line.startswith("socks"):
                    line = f"http://{line}"
                proxies.append(line)
        console.print(f"  [cyan][PROXY] Loaded {len(proxies)} proxies from {filepath}[/cyan]")
        return proxies
    except FileNotFoundError:
        console.print(f"  [red][PROXY] File not found: {filepath}[/red]")
        return []


# ═══════════════════════════════════════════════════════════════
#  PROXY VALIDATOR
# ═══════════════════════════════════════════════════════════════

def validate_proxy(proxy_url, results, lock):
    """Tests a single proxy and adds to results if working"""
    proxies = {"http": proxy_url, "https": proxy_url}
    try:
        start = time.time()
        r = requests.get(TEST_URL, proxies=proxies, timeout=TEST_TIMEOUT, verify=False)
        elapsed = round(time.time() - start, 2)
        if r.status_code == 200:
            with lock:
                results.append({"url": proxy_url, "ip": r.text.strip(), "speed": elapsed})
    except Exception:
        pass


def validate_all(proxies, max_threads=20):
    """
    Validates all proxies concurrently.
    Returns list of working proxies sorted by speed.
    """
    console.print(f"  [cyan][PROXY] Validating {len(proxies)} proxies...[/cyan]")
    results = []
    lock    = threading.Lock()
    threads = []

    for proxy in proxies:
        t = threading.Thread(target=validate_proxy, args=(proxy, results, lock))
        threads.append(t)
        t.start()
        if len(threads) >= max_threads:
            for t in threads:
                t.join()
            threads = []

    for t in threads:
        t.join()

    results.sort(key=lambda x: x["speed"])
    console.print(f"  [green][PROXY] {len(results)} working proxies found ✅[/green]")
    return results


# ═══════════════════════════════════════════════════════════════
#  PROXY POOL MANAGER
# ═══════════════════════════════════════════════════════════════

class ProxyPool:
    def __init__(self, proxy_file, validate=True):
        raw = load_proxies(proxy_file)
        if validate and raw:
            self.proxies = validate_all(raw)
        else:
            self.proxies = [{"url": p, "ip": "unknown", "speed": 0} for p in raw]

        self.index    = 0
        self.banned   = set()
        self.lock     = threading.Lock()

    def get_proxy(self):
        """Returns next working proxy"""
        with self.lock:
            attempts = 0
            while attempts < len(self.proxies):
                proxy = self.proxies[self.index % len(self.proxies)]
                self.index += 1
                attempts   += 1
                if proxy["url"] not in self.banned:
                    return {"http": proxy["url"], "https": proxy["url"]}, proxy["ip"]
        return None, None

    def ban_proxy(self, proxy_dict):
        """Marks a proxy as banned"""
        if proxy_dict:
            url = proxy_dict.get("https") or proxy_dict.get("http")
            if url:
                with self.lock:
                    self.banned.add(url)
                    console.print(f"  [yellow][PROXY] Banned: {url}[/yellow]")

    def available(self):
        return len(self.proxies) - len(self.banned)

    def has_proxies(self):
        return self.available() > 0
