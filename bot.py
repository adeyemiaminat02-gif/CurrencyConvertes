from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update
import asyncio

async def background_heavy_task(context: ContextTypes.DEFAULT_TYPE):
    """This runs in the background non-blockingly."""
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    amount = job_data["amount"]

    # Simulate heavy processing or API calls
    await asyncio.sleep(5)

    # Push result back to user
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Your background calculation for {amount} USD is complete!"
    )

async def convert_background_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by user command, delegates to background job."""
    chat_id = update.effective_chat.id

    # Queue job to run once after 1 second delay
    context.job_queue.run_once(
        background_heavy_task,
        when=1,
        data={"chat_id": chat_id, "amount": 100}
    )

    await update.message.reply_text("⏳ Your request has been queued! We will notify you shortly.")
