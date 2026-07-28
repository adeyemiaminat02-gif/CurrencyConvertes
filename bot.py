import logging
import os
import sys
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# 1. CONFIGURE LOGGING (Explicitly flush output to stdout for Render)
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 2. COMMAND & MESSAGE HANDLERS
# ---------------------------------------------------------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    logger.info(f"Received /start command from user: {user.username} ({user.id})")
    await update.message.reply_text(
        f"Hello {user.first_name}! 👋\nYour Telegram bot is successfully up and running on Render!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /help command."""
    await update.message.reply_text("Send me any text message and I will echo it back to you!")

async def echo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echoes user text messages back to them."""
    if update.message and update.message.text:
        logger.info(f"Received message from {update.effective_user.id}: {update.message.text}")
        await update.message.reply_text(f"You said: {update.message.text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs any errors caused by updates."""
    logger.error(f"Update '{update}' caused error: {context.error}", exc_info=context.error)


# ---------------------------------------------------------------------------
# 3. MAIN APPLICATION INITIALIZATION
# ---------------------------------------------------------------------------
def main() -> None:
    # Read token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        logger.critical(
            "FATAL ERROR: 'TELEGRAM_BOT_TOKEN' environment variable is missing!"
        )
        logger.critical("Please set TELEGRAM_BOT_TOKEN in your Render service Environment tab.")
        sys.exit(1)

    logger.info("Starting Telegram Bot build sequence...")

    # Initialize python-telegram-bot Application
    app = ApplicationBuilder().token(token).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler)
    )

    # Register global error handler
    app.add_error_handler(error_handler)

    # Start the bot in continuous polling mode
    logger.info("Bot configured successfully. Beginning polling loop...")
    
    # drop_pending_updates=True drops old messages sent while the bot was offline
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Uncaught exception caused application failure: {e}", exc_info=True)
        sys.exit(1)
