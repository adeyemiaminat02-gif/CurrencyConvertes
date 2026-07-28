import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME: str = os.getenv("BOT_USERNAME", "CurrencyConvertesbot")
    EXCHANGE_API_KEY: str = os.getenv("EXCHANGE_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/bot.db")
    DEFAULT_BASE: str = os.getenv("DEFAULT_BASE", "USD")
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "20.0"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # API URL setup (Using open rates from exchange-api / exchangerate-api)
    API_BASE_URL: str = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_API_KEY}"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger("CurrencyBot")
