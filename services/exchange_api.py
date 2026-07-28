import httpx
from typing import Dict, Any, Optional
from cachetools import TTLCache
from config import Config, logger

class ExchangeRateService:
    def __init__(self):
        # Cache exchange rates for 10 minutes (600 seconds)
        self.cache = TTLCache(maxsize=100, ttl=600)

    async def get_rates(self, base_currency: str = "USD") -> Optional[Dict[str, float]]:
        base_currency = base_currency.upper()
        if base_currency in self.cache:
            return self.cache[base_currency]

        url = f"{Config.API_BASE_URL}/latest/{base_currency}"
        try:
            async with httpx.AsyncClient(timeout=Config.REQUEST_TIMEOUT) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("result") == "success":
                    rates = data.get("conversion_rates", {})
                    self.cache[base_currency] = rates
                    return rates
                else:
                    logger.error(f"API Error response: {data}")
                    return None
        except Exception as e:
            logger.error(f"Failed to fetch exchange rates: {e}")
            return None

    async def convert(self, amount: float, from_curr: str, to_curr: str) -> Optional[Dict[str, Any]]:
        rates = await self.get_rates(from_curr)
        if not rates or to_curr.upper() not in rates:
            return None
        
        rate = rates[to_curr.upper()]
        converted_amount = amount * rate
        return {
            "amount": amount,
            "from": from_curr.upper(),
            "to": to_curr.upper(),
            "rate": rate,
            "result": converted_amount
        }

exchange_service = ExchangeRateService()
