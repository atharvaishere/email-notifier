import asyncio
from telegram import Bot

bot_token = "7618111671:AAHTCjauy7CiCw6bTfcQzM9ChboA90fmKYw"  
chat_id = "955773698"  # your correct chat id

async def test_bot():
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text="✅ Hello from your bot!")

asyncio.run(test_bot())