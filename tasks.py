import os
from celery import Celery
import httpx

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("bot_tasks", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task
def process_heavy_conversion(user_id: int, from_curr: str, to_curr: str, amount: float):
    """Offloaded Celery worker task."""
    # Execute heavy computation or external API synchronization here
    result = amount * 0.92  # Example result
    
    # Send notification back via Telegram Bot API HTTP directly
    bot_token = os.getenv("BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    httpx.post(url, json={
        "chat_id": user_id,
        "text": f"📊 Background Result: {amount} {from_curr} = {result} {to_curr}"
    })
    return result
