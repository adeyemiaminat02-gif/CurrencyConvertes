from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "👋 **Welcome to CurrencyConverterBot!**\n\n"
        "Convert over 150 currencies instantly with real-time exchange rates.\n\n"
        "💡 **Quick Examples:**\n"
        "• `100 USD to EUR`\n"
        "• `500 GBP to NGN`\n\n"
        "Use /help to see all available features."
    )
    keyboard = [
        [InlineKeyboardButton("💱 Convert", callback_data="btn_help"), InlineKeyboardButton("📊 Supported Currencies", callback_data="btn_currencies")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)
