import asyncio

import redis.asyncio as aioredis
from fastapi import HTTPException
from typing import Optional

from sqlalchemy.exc import IntegrityError

from ..repositories.url_repository import url_repository
from ..utils.base62 import generate_short_code
from ..config import get_settings

settings = get_settings()


def _format_response(url) -> dict:
    """Format URL response"""
    return {
        "short_code": url.short_code,
        "short_url": f"{settings.base_url}/{url.short_code}",
        "original_url": url.original_url,
        "created_at": url.created_at,
        "last_accessed_at": url.last_accessed_at,
        "click_count": url.click_count,
        "is_active": url.is_active
    }


class URLService:
    def __init__(self):
        self.repository = url_repository
        self.redis = aioredis.from_url(settings.redis_url, decode_responses=False)
        self.cache_ttl = settings.redis_ttl

    async def create_short_url(self, original_url: str, custom_alias: Optional[str], ip: str) -> dict:
        """Create shortened URL with idempotency"""
        # Check if URL already exists (idempotency)
        # Check if URL already exists (idempotency - first check)
        existing = await self.repository.get_by_original_url(original_url)
        if existing and existing.short_code != "temp":
            return _format_response(existing)

        # Check custom alias availability
        if custom_alias:
            existing_alias = await self.repository.get_by_short_code(custom_alias)
            if existing_alias:
                raise HTTPException(status_code=400, detail="Custom alias already taken")

        try:
            # Create URL entry with temp short_code
            url = await self.repository.create_url(original_url, custom_alias, ip)

            if custom_alias:
                url.short_code = custom_alias
            else:
                # Generate short code using ID
                url.short_code = generate_short_code(original_url, url.id, settings.short_code_length)

            # Update with actual short_code
            url = await self.repository.update_short_code(url.id, url.short_code)

            # Cache the mapping
            await self._cache_url(url.short_code, original_url)

            return _format_response(url)

        except IntegrityError:
            # Race condition occurred - another request created this URL
            # Retry with exponential backoff (10ms base delay, 3 retries)
            max_retries = 3
            delay_ms = 10  # 10 milliseconds base delay

            for attempt in range(max_retries):
                # Retrieve the existing entry from database
                existing = await self.repository.get_by_original_url(original_url)

                if existing and existing.short_code != "temp":
                    # Valid entry exists, cache and return it
                    await self._cache_url(existing.short_code, original_url)
                    return _format_response(existing)

                # If not the last attempt, wait before retry
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay_ms / 1000)  # Convert ms to seconds
                    delay_ms *= 2  # Exponential backoff: 10ms, 20ms, 40ms

            # All retries exhausted, entry still has temp short_code
            raise HTTPException(
                status_code=500,
                detail="Failed to create short URL due to race condition"
            )


    async def get_original_url(self, short_code: str) -> str:
        """Get original URL with caching for <10ms response"""
        # Try cache first (sub-millisecond lookup)
        cached = await self.redis.get(f"url:{short_code}")

        if cached:
            # Cache hit - increment async (don't wait)
            await self.repository.increment_click_count(short_code)
            return cached.decode('utf-8')

        # Cache miss - query database
        url = await self.repository.get_by_short_code(short_code)

        if not url:
            raise HTTPException(status_code=404, detail="URL not found")

        # Update cache for future requests
        await self._cache_url(short_code, url.original_url)

        # Increment click count
        await self.repository.increment_click_count(short_code)

        return url.original_url

    async def get_url_info(self, short_code: str) -> dict:
        """Get URL information"""
        url = await self.repository.get_by_short_code(short_code)

        if not url:
            raise HTTPException(status_code=404, detail="URL not found")

        return url

    async def list_urls(self, page: int, page_size: int) -> dict:
        """List URLs with pagination"""
        urls, total = await self.repository.get_paginated_urls(page, page_size)
        urls = [_format_response(url) for url in urls]
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "urls": urls
        }

    async def get_analytics(self) -> dict:
        """Get analytics data"""
        return await self.repository.get_analytics()

    async def delete_url(self, short_code: str) -> bool:
        """Delete URL"""
        # Remove from cache
        await self.redis.delete(f"url:{short_code}")

        # Soft delete from database
        return await self.repository.delete_url(short_code)

    async def _cache_url(self, short_code: str, original_url: str) -> None:
        """Cache URL mapping with TTL"""
        await self.redis.setex(
            f"url:{short_code}",
            self.cache_ttl,
            original_url
        )

    async def close(self):
        """Close connections"""
        await self.redis.close()


url_service = URLService()
