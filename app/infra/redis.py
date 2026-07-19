import logging
import os

import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

try:
    redis_client = redis.from_url(REDIS_URL)
except Exception as e:
    logging.getLogger("uvicorn.access").warning(
        f"Redis unavailable: could not connect to {REDIS_URL}: {e}"
    )
    redis_client = None

