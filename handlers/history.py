from telegram import Update
from telegram.ext import ContextTypes
from services.database_service import db_service

async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    records = await db_service.get_history(user_id)
    
    if not records:
        await update.message.reply_text("📜 You have no conversion history yet.")
        return

    text = "📜 **Your Recent Conversions:**\n\n"
    for r in records:
        text += f"• `{r.amount:,.2f} {r.from_currency}` ➔ `{r.converted_amount:,.2f} {r.to_currency}`\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")
