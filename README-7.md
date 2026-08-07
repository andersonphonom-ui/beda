# 💀 Beda

**Beda** is an advanced Python HTTPS brute force tool that handles all login scenarios automatically — CSRF tokens, sessions, IP rotation via Tor, rate limit detection, and smart success detection.

> ⚠️ **Disclaimer:** For educational purposes and authorized testing only.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 Auto Form Analysis | Detects username/password fields automatically |
| 🛡️ CSRF Handling | Fetches and submits CSRF token on every request |
| 🔄 Session Management | Maintains cookies and session between requests |
| 🧅 IP Rotation | Changes IP via Tor every N attempts |
| ⚡ Rate Limit Detection | Detects 429, captcha, and IP blocks |
| 🎯 Smart Success Detection | URL redirect, response diff, custom text |
| ⏱️ Delay Support | Add delay between requests to avoid detection |
| 📋 Custom Headers/Data | Add any extra headers or POST fields |

---

## 📦 Installation

```bash
git clone https://github.com/andersonphonom-ui/beda.git
cd beda
pip install -r requirements.txt --break-system-packages
sudo cp main.py banner.py brute.py analyzer.py tor_manager.py /usr/local/bin/
sudo mv /usr/local/bin/main.py /usr/local/bin/beda
sudo chmod +x /usr/local/bin/beda
```

---

## 🚀 Usage

```bash
# Basic scan — auto detects everything
beda -t https://site.com/login -u admin -w rockyou.txt

# With verbose
beda -t https://site.com/login -u admin -w rockyou.txt -x

# With Tor IP rotation every 2 attempts
beda -t https://site.com/login -u admin -w rockyou.txt --tor

# Custom rotation interval
beda -t https://site.com/login -u admin -w rockyou.txt --tor --rotate-every 5

# Add delay between requests
beda -t https://site.com/login -u admin -w rockyou.txt --delay 2

# Custom fields
beda -t https://site.com/login -u admin -w rockyou.txt --user-field email --pass-field pwd

# Custom success/fail text
beda -t https://site.com/login -u admin -w rockyou.txt --fail-text "Invalid credentials"

# Extra headers
beda -t https://site.com/login -u admin -w rockyou.txt --header "X-Requested-With: XMLHttpRequest"

# Extra POST data
beda -t https://site.com/login -u admin -w rockyou.txt --data "remember=1"
```

---

## 📁 Project Structure

```
beda/
├── main.py         # CLI entry point
├── banner.py       # ASCII art banner
├── brute.py        # Main brute force engine
├── analyzer.py     # Form analysis & success detection
├── tor_manager.py  # Tor IP rotation
└── requirements.txt
```

---

## 👨‍💻 Author

**Youssef Mediouni**
- YouTube: [PH4nt0m CYber](https://youtube.com/@PH4nt0mCYber)
- GitHub: [@andersonphonom-ui](https://github.com/andersonphonom-ui)

---

## 📄 License

MIT License
