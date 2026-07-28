from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.validation import parse_conversion_input
from services.exchange_api import exchange_service
from services.formatter import format_conversion_result
from services.database_service import db_service

def get_conversion_keyboard(from_curr: str, to_curr: str, amount: float):
    keyboard = [
        [
            InlineKeyboardButton("🔄 Swap", callback_data=f"swap_{from_curr}_{to_curr}_{amount}"),
            InlineKeyboardButton("🔁 Refresh", callback_data=f"refresh_{from_curr}_{to_curr}_{amount}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def text_conversion_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    parsed = parse_conversion_input(update.message.text)
    if not parsed:
        return  # Ignore messages not matching conversion format

    amount, from_curr, to_curr = parsed

    if amount <= 0:
        await update.message.reply_text("⚠️ Amount must be greater than zero.")
        return

    res = await exchange_service.convert(amount, from_curr, to_curr)
    if not res:
        await update.message.reply_text("❌ Invalid currency codes or service temporarily unavailable.")
        return

    # Save to history DB
    await db_service.add_history(update.effective_user.id, amount, from_curr, to_curr, res['result'])

    output = format_conversion_result(amount, from_curr, to_curr, res['rate'], res['result'])
    keyboard = get_conversion_keyboard(from_curr, to_curr, amount)

    await update.message.reply_text(output, parse_mode="Markdown", reply_markup=keyboard)

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "btn_help":
        await query.message.reply_text("Send an amount and currencies (e.g. `100 USD to EUR`) to convert instantly.")
    elif data == "btn_currencies":
        from handlers.currencies import currencies_handler
        await currencies_handler(update, context)
    elif data.startswith("swap_") or data.startswith("refresh_"):
        parts = data.split("_")
        action, from_curr, to_curr, amount_str = parts[0], parts[1], parts[2], float(parts[3])

        if action == "swap":
            from_curr, to_curr = to_curr, from_curr

        res = await exchange_service.convert(amount_str, from_curr, to_curr)
        if res:
            output = format_conversion_result(amount_str, from_curr, to_curr, res['rate'], res['result'])
            keyboard = get_conversion_keyboard(from_curr, to_curr, amount_str)
            await query.edit_message_text(output, parse_mode="Markdown", reply_markup=keyboard)
