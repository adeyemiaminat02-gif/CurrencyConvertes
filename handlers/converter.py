from telegram import Update
from telegram.ext import ContextTypes
from tasks import process_heavy_conversion

async def async_heavy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Push task to Celery queue immediately without blocking bot execution
    process_heavy_conversion.delay(user_id, "USD", "EUR", 1000.0)

    await update.message.reply_text("📥 Your request was sent to our processing engine. Standby for results!")
