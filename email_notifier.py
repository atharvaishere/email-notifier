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
GMAIL_TOKEN_JSON = os.environ.get("GMAIL_TOKEN_JSON")
# Validate env vars
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram Bot token or Chat ID is missing.")

if not GMAIL_TOKEN_JSON:
    raise ValueError("❌ Gmail token is missing.")

# ----- GMAIL AUTH -----
def get_gmail_service():
    creds = None
    token_base64 = os.environ.get("GMAIL_TOKEN_JSON")
    token_data = base64.b64decode(os.environ.get("GMAIL_TOKEN_JSON"))
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