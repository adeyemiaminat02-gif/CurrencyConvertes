from telegram import Update
from telegram.ext import ContextTypes
from services.validation import SUPPORTED_CURRENCIES

async def currencies_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    curr_list = ", ".join(sorted(list(SUPPORTED_CURRENCIES)))
    text = f"🌍 **Supported Major Currencies:**\n\n`{curr_list}`\n\n*Supports all standard ISO-4217 international currencies!*"
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode="Markdown")
