import re
from typing import Optional, Tuple

SUPPORTED_CURRENCIES = {
    "USD", "EUR", "GBP", "NGN", "CAD", "AUD", "JPY", "CNY", "INR", 
    "CHF", "AED", "SAR", "ZAR", "SGD", "HKD", "BRL", "MXN", "RUB"
}

def parse_conversion_input(text: str) -> Optional[Tuple[float, str, str]]:
    # Regex matching pattern like: 100 USD to EUR or 100 USD EUR
    pattern = r"^(\d+(?:\.\d+)?)\s*([A-Za-z]{3})\s*(?:to\s*)?([A-Za-z]{3})$"
    match = re.match(pattern, text.strip(), re.IGNORECASE)
    
    if match:
        amount, from_c, to_c = match.groups()
        return float(amount), from_c.upper(), to_c.upper()
    return None
