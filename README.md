# 📬 Gmail AI Notifier with Telegram & Bark Integration

Automatically monitors your Gmail inbox for important job-related emails and sends real-time alerts to:
- 📱 **Telegram**
- 📳 **Bark (iOS Push Notifications)**

Built by Atharva Shrivastava to streamline job alerts and cut the noise. 🧠⚙️

---

## ✨ Features
- ✅ Reads Gmail inbox using Gmail API
- 🔍 Filters out promotional, social, and irrelevant emails
- 🧠 Detects only important messages with keywords like company names
- 🛑 Blocks known noisy sources (LinkedIn Job Alerts, Quora, etc.)
- 📩 Sends notification via Telegram
- 📱 Sends push notification via Bark (iOS only)
- ☁️ Runs as a background service on macOS

---

## 🔧 Tech Stack
- Python 3.9+
- Gmail API
- Telegram Bot API
- Bark Push API
- `asyncio` for async message checks
- `BeautifulSoup` for HTML email parsing

---

## 🛠 Setup

### 1. Clone the repo
```bash
git clone https://github.com/atharva-ai/email-notifier.git
cd email-notifier
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Gmail API Auth
- Follow Google OAuth2 flow.
- Save the `token.json` file
- Base64 encode it:
  ```bash
  base64 token.json > token_base64.txt
  ```
- Paste its content into `GMAIL_TOKEN_JSON` in `email_notifier.py`

---

## ⚙️ Configuration

### email_notifier.py
- `TELEGRAM_BOT_TOKEN` → From [BotFather](https://t.me/botfather)
- `TELEGRAM_CHAT_ID` → Your user ID (use a bot to get it)
- `device_key` in `send_bark_notification()` → Your [Bark](https://day.app/) token
- `COMPANY_KEYWORDS` → List of companies to watch for
- `BLOCKED_SENDERS` & `BLOCKED_KEYWORDS` → Noise filters

---

## 🖥️ Run as Background Service (macOS)

### 1. Create launcher script
**start_gmail_monitor.sh**
```bash
#!/bin/bash
cd /Users/xxxx/Desktop/email-notifier
/usr/bin/python3 email_notifier.py
```

### 2. Create launchd plist
**~/Library/LaunchAgents/com.atharva.gmailmonitor.plist**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.atharva.gmailmonitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/xxxx/Desktop/email-notifier/start_gmail_monitor.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/gmailmonitor.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/gmailmonitor.err</string>
</dict>
</plist>
```

### 3. Load the service
```bash
launchctl load ~/Library/LaunchAgents/com.atharva.gmailmonitor.plist
```

To stop:
```bash
launchctl unload ~/Library/LaunchAgents/com.atharva.gmailmonitor.plist
```

---

## ✅ Status
- ✅ Telegram push working
- ✅ Bark working with clean formatted messages
- ✅ Filters in place for noise and unneeded updates
- ✅ Avoids duplicate alerts using `notified_ids.json`

---

## 🧠 Coming Soon
- WhatsApp integration (Twilio / 360Dialog if free options found)
- Clickable URLs in push
- Night mode to pause alerts

---

## 🪪 License
MIT

---

## 💬 Questions?
Reach out on Telegram: `@atharva_ai` or raise an issue!



Last updated: 2025-04-17 -