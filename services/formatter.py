from datetime import datetime

def format_conversion_result(amount: float, from_curr: str, to_curr: str, rate: float, result: float) -> str:
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"💱 **Currency Conversion**\n\n"
        f"💵 **{amount:,.2f} {from_curr}** = **{result:,.2f} {to_curr}**\n\n"
        f"📈 **Exchange Rate:** 1 {from_curr} = {rate:.4f} {to_curr}\n"
        f"🕒 **Updated:** {now}"
    )
