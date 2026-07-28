from telegram import Update
from telegram.ext import ContextTypes
from services.exchange_api import exchange_service

async def rate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Usage: `/rate USD EUR`", parse_mode="Markdown")
        return
    
    base, target = args[0].upper(), args[1].upper()
    res = await exchange_service.convert(1.0, base, target)
    if not res:
        await update.message.reply_text("❌ Failed to fetch exchange rate. Check currency codes.")
        return

    await update.message.reply_text(f"📈 **Exchange Rate:** 1 {base} = `{res['rate']:.4f} {target}`", parse_mode="Markdown")
