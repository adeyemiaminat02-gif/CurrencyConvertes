import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import Config, logger
from database import init_db

# Handlers
from handlers.start import start_handler
from handlers.help import help_handler
from handlers.about import about_handler
from handlers.currencies import currencies_handler
from handlers.history import history_handler
from handlers.rates import rate_handler
from handlers.converter import text_conversion_handler, callback_query_handler

async def main():
    logger.info("Initializing Database...")
    await init_db()

    logger.info("Building Telegram Application...")
    app = ApplicationBuilder().token(Config.BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("about", about_handler))
    app.add_handler(CommandHandler("currencies", currencies_handler))
    app.add_handler(CommandHandler("history", history_handler))
    app.add_handler(CommandHandler("rate", rate_handler))

    # Text & Callbacks
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_conversion_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    logger.info("Bot started successfully. Running polling...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
