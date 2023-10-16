from redis import Redis, asyncio as aioredis
from tools.config.app_settings import app_settings

# Global Redis Connection Pool from url
redis_client:Redis = aioredis.from_url(app_settings.redis_url)