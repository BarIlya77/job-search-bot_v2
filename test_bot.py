# test_bot.py
import logging
from telegram.ext import Application, CommandHandler

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    await update.message.reply_text("Test bot works!")

def main():
    token = "8500374007:AAGZoDZtJxR84J7jmR32laT0eMyo9KeI8oI"  # временно вставьте токен прямо здесь
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
