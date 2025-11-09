import redis.asyncio as aioredis
from fastapi import Request, HTTPException

class RateLimiter:
    def __init__(self, redis_url: str, limit: int, window: int):
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.limit = limit
        self.window = window

    async def check_rate_limit(self, request: Request) -> None:
        """Check if request exceeds rate limit"""
        # Get client IP
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"

        # Get current count
        current = await self.redis.get(key)

        if current is None:
            # First request in window
            await self.redis.setex(key, self.window, 1)
        elif int(current) >= self.limit:
            # Rate limit exceeded
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.limit} requests per {self.window} seconds."
            )
        else:
            # Increment counter
            await self.redis.incr(key)

    async def close(self):
        """Close Redis connection"""
        await self.redis.close()
