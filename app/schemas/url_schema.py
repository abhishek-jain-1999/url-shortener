from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional

class URLCreate(BaseModel):
    target_url: HttpUrl
    custom_alias: Optional[str] = Field(None, max_length=50, pattern="^[a-zA-Z0-9_-]+$")

class URLResponse(BaseModel):
    short_code: str
    short_url: Optional[str]
    original_url: str
    created_at: datetime

    class Config:
        from_attributes = True

class URLInfo(URLResponse):
    click_count: int
    last_accessed_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class URLListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    urls: list[URLInfo]

class AnalyticsResponse(BaseModel):
    total_urls: int
    total_clicks: int
    active_urls: int
    clicks_today: int
