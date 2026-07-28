from telegram import Update
from telegram.ext import ContextTypes

async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ **About @CurrencyConvertesbot**\n\n"
        "High-performance Telegram bot offering real-time currency conversions.\n"
        "Powered by Python 3.12, `python-telegram-bot` v22, and SQLite.\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
