import os
import base64
import pickle
import time
import asyncio
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from telegram import Bot

# ----- CONFIGURATION -----
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
COMPANY_KEYWORDS = ['Compass Education', 'Swappsi', 'Arista Networks', '']  # <- Add more if needed
CHECK_INTERVAL = 3600  # in seconds

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GMAIL_TOKEN_JSON = """gASV5AMAAAAAAACMGWdvb2dsZS5vYXV0aDIuY3JlZGVudGlhbHOUjAtDcmVkZW50aWFsc5STlCmBlH2UKIwFdG9rZW6UjN55YTI5LmEwQVpZa05aZ0hJd1RrcjBYTmp4c1M5R0o4dk9JUVZ0Tlc4ZVBkdjdTdl81MHB4MGpnYWw2Ny1iN1ZGbzZhT1FYdmJCTUxvS21pZ1FUcU1TSDJ4S2ZoLXBoa1M3ZDZTSXhXcmdfei01QVBHZTBib0J2R3YwNmlBN2RERDliZS05cFNiSFBJN0xpakI1TjBuTkhPVmV4aVlFOEFwV0FLWnpONFp3WWVXQTcwYUNnWUtBVElTQVJJU0ZRSEdYMk1pTU9QZGt1ZllveTJzd0s5d0NHbzN5dzAxNzWUjAZleHBpcnmUjAhkYXRldGltZZSMCGRhdGV0aW1llJOUQwoH6QQPBCEbBDgZlIWUUpSMEV9xdW90YV9wcm9qZWN0X2lklE6MD190cnVzdF9ib3VuZGFyeZROjBBfdW5pdmVyc2VfZG9tYWlulIwOZ29vZ2xlYXBpcy5jb22UjBlfdXNlX25vbl9ibG9ja2luZ19yZWZyZXNolImMB19zY29wZXOUXZSMLmh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL2F1dGgvZ21haWwucmVhZG9ubHmUYYwPX2RlZmF1bHRfc2NvcGVzlE6MDl9yZWZyZXNoX3Rva2VulIxnMS8vMDNKR0ZXS2lreXlOOENnWUlBUkFBR0FNU053Ri1MOUlySlgyTDhkbEkxbExCVkRlbW9FcV9JazZRWUNrRkM1cU1Rc2FZWFNLS21NeGNTQk1SMnVoRkNxOWlxaGU3eC02ekpTSZSMCV9pZF90b2tlbpROjA9fZ3JhbnRlZF9zY29wZXOUXZSMLmh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL2F1dGgvZ21haWwucmVhZG9ubHmUYYwKX3Rva2VuX3VyaZSMI2h0dHBzOi8vb2F1dGgyLmdvb2dsZWFwaXMuY29tL3Rva2VulIwKX2NsaWVudF9pZJSMSDc0MDc4ODYzMjY4Mi01MXEydWoybmRlNzk2MDFxZnMya290YjBjdWx0b3N2MC5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbZSMDl9jbGllbnRfc2VjcmV0lIwjR09DU1BYLS1tcmd3aG9GWnJKaldSV05LcHExSFZPSld4dDiUjAtfcmFwdF90b2tlbpROjBZfZW5hYmxlX3JlYXV0aF9yZWZyZXNolImMCF9hY2NvdW50lIwAlIwPX2NyZWRfZmlsZV9wYXRolE51Yi4="""
# Validate env vars
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram Bot token or Chat ID is missing.")

if not GMAIL_TOKEN_JSON:
    raise ValueError("❌ Gmail token is missing.")

# ----- GMAIL AUTH -----
def get_gmail_service():
    creds = None
    token_base64 = os.environ.get("GMAIL_TOKEN_JSON")
    token_data = base64.b64decode(GMAIL_TOKEN_JSON)
    creds = pickle.load(io.BytesIO(token_data))
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            import json
            creds_dict = json.loads(os.environ.get("GMAIL_CREDENTIALS_JSON"))
            with open("temp_credentials.json", "w") as f:
                json.dump(creds_dict, f)
            flow = InstalledAppFlow.from_client_secrets_file('temp_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

# ----- EMAIL CHECK FUNCTION -----
def get_latest_email_snippets(service, max_results=5):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=max_results).execute()
    messages = results.get('messages', [])
    snippets = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = msg_data.get('snippet', '')
        snippets.append(snippet)
    return snippets

# ----- TELEGRAM NOTIFICATION -----
async def notify_via_telegram(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

# ----- MAIN LOOP -----
async def main_loop():
    service = get_gmail_service()
    seen_snippets = set()

    while True:
        snippets = get_latest_email_snippets(service)
        for snippet in snippets:
            if snippet not in seen_snippets:
                for company in COMPANY_KEYWORDS:
                    if company.lower() in snippet.lower():
                        message = f"📩 New email related to *{company}*:\n\n{snippet}"
                        await notify_via_telegram(message)
                        break
                seen_snippets.add(snippet)
        await asyncio.sleep(CHECK_INTERVAL)

# ----- RUN -----
if __name__ == '__main__':
    asyncio.run(main_loop())