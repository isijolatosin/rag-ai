import os

import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

# Redis setup
REDIS_URL = os.environ.get("REDIS_URL")
redis = aioredis.from_url(REDIS_URL, decode_responses=True)

async def get_cached_response(query: str):
    cached = await redis.get(f"cache:{query}")
    return cached