import os
import re
import sys
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import httpx
from cachetools import TTLCache
from sqlalchemy import BigInteger, String, Float, DateTime, func, select, desc
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# 1. LOGGING & CONFIGURATION
# ---------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger("CurrencyBot")

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "20.0"))

SUPPORTED_CURRENCIES = {
    "USD", "EUR", "GBP", "NGN", "CAD", "AUD", "JPY", "CNY", "INR",
    "CHF", "AED", "SAR", "ZAR", "SGD", "HKD", "BRL", "MXN", "RUB"
}

# ---------------------------------------------------------------------------
# 2. DATABASE SETUP (SQLAlchemy Async)
# ---------------------------------------------------------------------------
# Ensure database path exists for SQLite
if DATABASE_URL.startswith("sqlite+aiosqlite:///./"):
    os.makedirs("./data", exist_ok=True)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class ConversionHistory(Base):
    __tablename__ = "conversion_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[float] = mapped_column(Float)
    from_currency: Mapped[str] = mapped_column(String(3))
    to_currency: Mapped[str] = mapped_column(String(3))
    converted_amount: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_history(user_id: int, amount: float, from_curr: str, to_curr: str, result: float):
    async with AsyncSessionLocal() as session:
        entry = ConversionHistory(
            user_id=user_id,
            amount=amount,
            from_currency=from_curr,
            to_currency=to_curr,
            converted_amount=result
        )
        session.add(entry)
        await session.commit()

        # Retain only the latest 10 records per user
        stmt = select(ConversionHistory).where(ConversionHistory.user_id == user_id).order_by(desc(ConversionHistory.timestamp))
        res = await session.execute(stmt)
        records = res.scalars().all()
        if len(records) > 10:
            for old_record in records[10:]:
                await session.delete(old_record)
            await session.commit()


async def get_history(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(ConversionHistory).where(ConversionHistory.user_id == user_id).order_by(desc(ConversionHistory.timestamp)).limit(10)
        res = await session.execute(stmt)
        return res.scalars().all()


# ---------------------------------------------------------------------------
# 3. EXCHANGE RATE SERVICE (With Cache & Fallback API)
# ---------------------------------------------------------------------------
class ExchangeRateService:
    def __init__(self):
        # 10 minute cache TTL
        self.cache = TTLCache(maxsize=100, ttl=600)

    async def get_rates(self, base: str = "USD") -> Optional[Dict[str, float]]:
        base = base.upper()
        if base in self.cache:
            return self.cache[base]

        # Use ExchangeRate-API if API key exists, otherwise fallback to Frankfurter API
        if EXCHANGE_API_KEY:
            url = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}/latest/{base}"
        else:
            url = f"https://api.frankfurter.app/latest?from={base}"

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                if EXCHANGE_API_KEY:
                    rates = data.get("conversion_rates", {})
                else:
                    rates = data.get("rates", {})
                    rates[base] = 1.0  # Base rate self-reference

                if rates:
                    self.cache[base] = rates
                    return rates
        except Exception as e:
            logger.error(f"Error fetching exchange rates for {base}: {e}")
        
        return None

    async def convert(self, amount: float, from_curr: str, to_curr: str) -> Optional[Dict[str, Any]]:
        from_curr, to_curr = from_curr.upper(), to_curr.upper()
        rates = await self.get_rates(from_curr)
        
        if not rates or to_curr not in rates:
            return None

        rate = rates[to_curr]
        result = amount * rate
        return {
            "amount": amount,
            "from": from_curr,
            "to": to_curr,
            "rate": rate,
            "result": result
        }


exchange_service = ExchangeRateService()


# ---------------------------------------------------------------------------
# 4. HELPER FUNCTIONS & UI KEYBOARDS
# ---------------------------------------------------------------------------
def parse_input(text: str):
    # Matches patterns like "100 USD to EUR", "500 GBP NGN", "50.5 CAD to JPY"
    pattern = r"^(\d+(?:\.\d+)?)\s*([A-Za-z]{3})\s*(?:to\s*)?([A-Za-z]{3})$"
    match = re.match(pattern, text.strip(), re.IGNORECASE)
    if match:
        amount, from_curr, to_curr = match.groups()
        return float(amount), from_curr.upper(), to_curr.upper()
    return None


def format_result(amount: float, from_curr: str, to_curr: str, rate: float, result: float) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"💱 **Currency Conversion**\n\n"
        f"💵 **{amount:,.2f} {from_curr}** = **{result:,.2f} {to_curr}**\n\n"
        f"📈 **Exchange Rate:** 1 {from_curr} = `{rate:.4f} {to_curr}`\n"
        f"🕒 **Updated:** {now}"
    )


def get_action_keyboard(from_curr: str, to_curr: str, amount: float) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🔄 Swap", callback_data=f"swap_{from_curr}_{to_curr}_{amount}"),
            InlineKeyboardButton("🔁 Refresh", callback_data=f"refresh_{from_curr}_{to_curr}_{amount}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------------------------------------------------------------------------
# 5. TELEGRAM COMMAND & MESSAGE HANDLERS
# ---------------------------------------------------------------------------
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 **Welcome to @CurrencyConvertesbot!**\n\n"
        "Convert over 150+ currencies instantly with real-time exchange rates.\n\n"
        "💡 **How to use:**\n"
        "Type your conversion directly into the chat:\n"
        "• `100 USD to EUR`\n"
        "• `500 GBP to NGN`\n"
        "• `1000 JPY CAD`\n\n"
        "Use /help to see all available commands."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📖 **Currency Converter Instructions**\n\n"
        "• **Convert:** Send messages like `100 USD to EUR`\n"
        "• **/rate <BASE> <TARGET>:** Get current rate (e.g., `/rate USD EUR`)\n"
        "• **/currencies:** View supported major currencies\n"
        "• **/history:** View your last 10 conversions\n"
        "• **/about:** Info about this bot"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def about_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "ℹ️ **About @CurrencyConvertesbot**\n\n"
        "High-performance currency conversion bot built with Python 3.12+.\n"
        "Features async request pipelines, rate caching, and multi-currency support."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def currencies_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    curr_list = ", ".join(sorted(list(SUPPORTED_CURRENCIES)))
    msg = f"🌍 **Supported Major Currencies:**\n\n`{curr_list}`\n\n_Supports all standard ISO-4217 international currencies!_"
    await update.message.reply_text(msg, parse_mode="Markdown")


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    records = await get_history(update.effective_user.id)
    if not records:
        await update.message.reply_text("📜 You have no conversion history yet.")
        return

    msg = "📜 **Your Recent Conversions:**\n\n"
    for r in records:
        msg += f"• `{r.amount:,.2f} {r.from_currency}` ➔ `{r.converted_amount:,.2f} {r.to_currency}`\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def rate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ **Usage:** `/rate USD EUR`", parse_mode="Markdown")
        return

    base, target = args[0].upper(), args[1].upper()
    res = await exchange_service.convert(1.0, base, target)
    if not res:
        await update.message.reply_text("❌ Could not fetch exchange rate. Check the currency codes.")
        return

    await update.message.reply_text(
        f"📈 **Exchange Rate:** 1 {base} = `{res['rate']:.4f} {target}`",
        parse_mode="Markdown"
    )


async def text_conversion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    parsed = parse_input(update.message.text)
    if not parsed:
        return  # Ignore messages that don't match currency format

    amount, from_curr, to_curr = parsed

    if amount <= 0:
        await update.message.reply_text("⚠️ Amount must be greater than zero.")
        return

    res = await exchange_service.convert(amount, from_curr, to_curr)
    if not res:
        await update.message.reply_text("❌ Invalid currency codes or rate service unavailable.")
        return

    # Record conversion in history
    await add_history(update.effective_user.id, amount, from_curr, to_curr, res["result"])

    text_output = format_result(amount, from_curr, to_curr, res["rate"], res["result"])
    keyboard = get_action_keyboard(from_curr, to_curr, amount)

    await update.message.reply_text(text_output, parse_mode="Markdown", reply_markup=keyboard)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("swap_") or data.startswith("refresh_"):
        parts = data.split("_")
        action, from_curr, to_curr, amount_str = parts[0], parts[1], parts[2], float(parts[3])

        if action == "swap":
            from_curr, to_curr = to_curr, from_curr

        res = await exchange_service.convert(amount_str, from_curr, to_curr)
        if res:
            text_output = format_result(amount_str, from_curr, to_curr, res["rate"], res["result"])
            keyboard = get_action_keyboard(from_curr, to_curr, amount_str)
            await query.edit_message_text(text_output, parse_mode="Markdown", reply_markup=keyboard)


# ---------------------------------------------------------------------------
# 6. MAIN APPLICATION ENTRYPOINT
# ---------------------------------------------------------------------------
def main():
    if not BOT_TOKEN:
        logger.critical("FATAL: 'BOT_TOKEN' or 'TELEGRAM_BOT_TOKEN' environment variable is missing!")
        sys.exit(1)

    # Initialize SQLite database asynchronously
    import asyncio
    asyncio.run(init_db())

    logger.info("Building Telegram bot application...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("about", about_handler))
    app.add_handler(CommandHandler("currencies", currencies_handler))
    app.add_handler(CommandHandler("history", history_handler))
    app.add_handler(CommandHandler("rate", rate_handler))

    # Text & Callback Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_conversion_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))

    logger.info("Bot configured successfully. Running polling loop...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
