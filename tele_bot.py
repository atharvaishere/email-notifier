# rt asyncio
#  telegram.ext import Application, MessageHandler, filters
# 
# token = '7618111671:AAHTCjauy7CiCw6bTfcQzM9ChboA90fmKYw'
# 
# c def handle_message(update, context):
# chat_id = update.message.chat_id
# print(f"Chat ID: {chat_id}")
# await update.message.reply_text(f"Your chat ID is: {chat_id}")
# 
# c def main():
# application = Application.builder().token(bot_token).build()
# application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
# await application.initialize()
# await application.start()
# print("Bot is running... Send a message to it!")
# await application.updater.start_polling()
# await asyncio.Event().wait()
# 
# _name__ == '__main__':
# asyncio.run(main())


import asyncio
from telegram import Bot

bot_token = '7618111671:AAHTCjauy7CiCw6bTfcQzM9ChboA90fmKYw'
chat_id = '955773698'

async def main():
    bot = Bot(token=bot_token)
    await bot.send_message(chat_id=chat_id, text="Hello Atharva! Your bot is working 🎉")

if __name__ == '__main__':
    asyncio.run(main())