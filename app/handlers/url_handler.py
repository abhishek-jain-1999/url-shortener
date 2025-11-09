from fastapi import APIRouter, Request, Query
from fastapi.responses import RedirectResponse
from typing import Annotated

from ..schemas.url_schema import URLCreate, URLResponse
from ..services.url_service import url_service
from ..services.rate_limiter import RateLimiter
from ..config import get_settings

settings = get_settings()
router = APIRouter()

# Initialize rate limiter
rate_limiter = RateLimiter(
    redis_url=settings.redis_url,
    limit=settings.rate_limit_requests,
    window=settings.rate_limit_window
)


@router.post("/api/shorten", response_model=URLResponse, status_code=201)
async def create_short_url(
        url_data: Annotated[URLCreate, Query()],  # Changed to Query parameter,
        request: Request):
    """Create a shortened URL"""
    # Check rate limit
    await rate_limiter.check_rate_limit(request)

    # Get client IP
    client_ip = request.client.host

    # Create short URL
    result = await url_service.create_short_url(
        str(url_data.target_url),
        url_data.custom_alias,
        client_ip
    )

    return result


@router.get("/{short_code}")
async def redirect_to_url(short_code: str):
    """Redirect to original URL"""
    original_url = await url_service.get_original_url(short_code)
    return RedirectResponse(url=original_url, status_code=301)


@router.get("/api/info/{short_code}")
async def get_url_info(short_code: str):
    """Get URL information"""
    return await url_service.get_url_info(short_code)
