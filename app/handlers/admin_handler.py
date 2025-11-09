from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from ..schemas.url_schema import URLListResponse, AnalyticsResponse
from ..services.url_service import url_service
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/admin", tags=["admin"])

def verify_admin_token(authorization: Optional[str] = Header(None)):
    """Verify admin authentication token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = authorization.replace("Bearer ", "")
    if token != settings.admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    return token

@router.get("/urls", response_model=URLListResponse)
async def list_urls(
        page: int = 1,
        page_size: int = 20,
        token: str = Depends(verify_admin_token)
):
    """List all URLs with pagination (admin only)"""
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination parameters")

    return await url_service.list_urls(page, page_size)

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(token: str = Depends(verify_admin_token)):
    """Get analytics data (admin only)"""
    return await url_service.get_analytics()

@router.delete("/urls/{short_code}")
async def delete_url(short_code: str, token: str = Depends(verify_admin_token)):
    """Delete a shortened URL (admin only)"""
    deleted = await url_service.delete_url(short_code)

    if not deleted:
        raise HTTPException(status_code=404, detail="URL not found")

    return {"message": "URL deleted successfully"}
