from telegram import Update
from telegram.ext import ContextTypes

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **How to Use the Bot**\n\n"
        "1️⃣ **Direct Input:** Send messages like `100 USD to EUR`\n"
        "2️⃣ **/rate <BASE> <TARGET>** - Get direct rate (e.g. `/rate USD EUR`)\n"
        "3️⃣ **/currencies** - List supported currencies\n"
        "4️⃣ **/history** - View last 10 conversions\n"
        "5️⃣ **/about** - Details about this bot"
    )
    await update.message.reply_text(text, parse_mode="Markdown")
