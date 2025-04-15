import os
import base64
import pickle
import time
import asyncio
import json
import io
import re
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from telegram import Bot

import warnings
warnings.filterwarnings("ignore")

# ----- CONFIGURATION -----
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
COMPANY_KEYWORDS = ['Compass Education', 'Swappsi', 'Arista Networks', '']  # <- Add more if needed
CHECK_INTERVAL = 10  # in seconds

TELEGRAM_BOT_TOKEN = "7618111671:AAHTCjauy7CiCw6bTfcQzM9ChboA90fmKYw"
TELEGRAM_CHAT_ID = "955773698"
GMAIL_TOKEN_JSON = """gASV5AMAAAAAAACMGWdvb2dsZS5vYXV0aDIuY3JlZGVudGlhbHOUjAtDcmVkZW50aWFsc5STlCmBlH2UKIwFdG9rZW6UjN55YTI5LmEwQVpZa05aZ0hJd1RrcjBYTmp4c1M5R0o4dk9JUVZ0Tlc4ZVBkdjdTdl81MHB4MGpnYWw2Ny1iN1ZGbzZhT1FYdmJCTUxvS21pZ1FUcU1TSDJ4S2ZoLXBoa1M3ZDZTSXhXcmdfei01QVBHZTBib0J2R3YwNmlBN2RERDliZS05cFNiSFBJN0xpakI1TjBuTkhPVmV4aVlFOEFwV0FLWnpONFp3WWVXQTcwYUNnWUtBVElTQVJJU0ZRSEdYMk1pTU9QZGt1ZllveTJzd0s5d0NHbzN5dzAxNzWUjAZleHBpcnmUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH6QQPBCEbBDgZlIWUUpSMEV9xdW90YV9wcm9qZWN0X2lklE6MD190cnVzdF9ib3VuZGFyeZROjBBfdW5pdmVyc2VfZG9tYWlulIwOZ29vZ2xlYXBpcy5jb22UjBlfdXNlX25vbl9ibG9ja2luZ19yZWZyZXNolImMB19zY29wZXOUXZSMLmh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL2F1dGgvZ21haWwucmVhZG9ubHmUYYwPX2RlZmF1bHRfc2NvcGVzlE6MDl9yZWZyZXNoX3Rva2VulIxnMS8vMDNKR0ZXS2lreXlOOENnWUlBUkFBR0FNU053Ri1MOUlySlgyTDhkbEkxbExCVkRlbW9FcV9JazZRWUNrRkM1cU1Rc2FZWFNLS21NeGNTQk1SMnVoRkNxOWlxaGU3eC02ekpTSZSMCV9pZF90b2tlbpROjA9fZ3JhbnRlZF9zY29wZXOUXZSMLmh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL2F1dGgvZ21haWwucmVhZG9ubHmUYYwKX3Rva2VuX3VyaZSMI2h0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VulIwKX2NsaWVudF9pZJSMSDc0MDc4ODYzMjY4Mi01MXEydWoybmRlNzk2MDFxZnMya290YjBjdWx0b3N2MC5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbZSMDl9jbGllbnRfc2VjcmV0lIwjR09DU1BYLS1tcmd3aG9GWnJKaldSV05LcHExSFZPSld4dDiUjAtfcmFwdF90b2tlbpROjBZfZW5hYmxlX3JlYXV0aF9yZWZyZXNolImMCF9hY2NvdW50lIwAlIwPX2NyZWRfZmlsZV9wYXRolE51Yi4="""
NOTIFIED_IDS_FILE = "notified_ids.json"
# Validate env vars
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram Bot token or Chat ID is missing.")

if not GMAIL_TOKEN_JSON:
    raise ValueError("❌ Gmail token is missing.")

# ----- GMAIL AUTH -----
def get_gmail_service():
    token_data = base64.b64decode(GMAIL_TOKEN_JSON)
    creds = pickle.load(io.BytesIO(token_data))
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('gmail', 'v1', credentials=creds)
    

# ----- EMAIL CHECK FUNCTION -----
def load_notified_ids():
    if os.path.exists(NOTIFIED_IDS_FILE):
        try:
            with open(NOTIFIED_IDS_FILE, "r") as f:
                data = f.read().strip()
                if not data:
                    return set()
                return set(json.loads(data))
        except (json.JSONDecodeError, ValueError):
            print("⚠️ notified_ids.json is invalid. Starting with empty set.")
            return set()
    return set()

def save_notified_ids(notified_ids):
    with open(NOTIFIED_IDS_FILE, "w") as f:
        json.dump(list(notified_ids), f)

def clean_linkedin_email_body(body):
    lines = body.splitlines()
    filtered_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        if not line or any(keyword in line.lower() for keyword in ["unsubscribe", "email_job_alert", "job~alert"]):
            continue
        if line in seen:
            continue
        seen.add(line)
        filtered_lines.append(line)

    # Try to extract first job URL
    job_url = next((line for line in filtered_lines if "linkedin.com/jobs/view" in line), None)
    filtered_lines = filtered_lines[:5]  # Keep only the first few relevant lines

    if job_url:
        filtered_lines.append(f"🔗 View Job: {job_url}")

    return "\n".join(filtered_lines)

# ----- TELEGRAM NOTIFICATION -----
async def notify_via_telegram(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    max_length = 4000
    for i in range(0, len(message), max_length):
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message[i:i+max_length])
    

# ----- MAIN LOOP -----
async def main_loop():
    service = get_gmail_service()
    notified_ids = load_notified_ids()

    while True:
        query = "-category:social -category:promotions"
        results = service.users().messages().list(userId='me', q=query, labelIds=['INBOX'], maxResults=5).execute()
        messages = results.get('messages', [])

        for msg in messages:
            msg_id = msg['id']
            if msg_id in notified_ids:
                continue

            msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            payload = msg_data.get('payload', {})
            parts = payload.get('parts', [])
            body = ''

            for part in parts:
                mime_type = part.get('mimeType')
                body_data = part['body'].get('data')
                if mime_type == 'text/plain' and body_data:
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    break
                elif mime_type == 'text/html' and body_data:
                    html_content = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    body = soup.get_text()
                    break

            if not body:
                body = msg_data.get('snippet', '')

            lower_body = body.lower()
            if "application submitted" in lower_body or "we regret to inform you" in lower_body:
                continue

            for company in COMPANY_KEYWORDS:
                if company.lower() in body.lower():
                    clean_body = clean_linkedin_email_body(body)
                    message = f"\U0001F4E9 New email related to *{company}*:\n\n{clean_body}"
                    await notify_via_telegram(message)
                    break

            notified_ids.add(msg_id)
            save_notified_ids(notified_ids)

        await asyncio.sleep(CHECK_INTERVAL)
    
    

# ----- RUN -----
if __name__ == '__main__':
    asyncio.run(main_loop())