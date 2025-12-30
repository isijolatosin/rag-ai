import os
from datetime import datetime

import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

# Redis setup
REDIS_URL = os.environ.get("REDIS_URL")
redis = aioredis.from_url(REDIS_URL, decode_responses=True)

# Token estimation (~1 token per 4 chars)
def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4

def today_key() -> str:
    """Return today's date as a string YYYY-MM-DD"""
    return datetime.now().strftime("%Y-%m-%d")

async def get_tokens_used_today(user_id: str) -> int:
    key = f"tokens:{user_id}:{today_key()}"
    used = await redis.get(key)
    return int(used or 0)

async def add_tokens(user_id: str, tokens: int):
    key = f"tokens:{user_id}:{today_key()}"
    used = int(await redis.get(key) or 0)
    await redis.set(key, used + tokens, ex=60 * 60 * 24)