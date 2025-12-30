import os

import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

# Redis setup
REDIS_URL = os.environ.get("REDIS_URL")
redis = aioredis.from_url(REDIS_URL, decode_responses=True)

async def set_cached_response(query: str, response: str):
    await redis.set(
        f"cache:{query}",
        response,
        ex=60 * 60 * 24
    )