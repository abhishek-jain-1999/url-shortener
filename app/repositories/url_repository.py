from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, update, func, and_
from datetime import datetime
from typing import Optional, Any, Sequence

from ..models.url import URL, Base
from ..config import get_settings

settings = get_settings()

class URLRepository:
    def __init__(self):
        # print("settings.database_url :",settings.database_url)
        self.engine = create_async_engine(
            settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def create_tables(self):
        """Create database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async def get_by_short_code(self, short_code: str) -> Optional[URL]:
        """Retrieve URL by short code"""
        async with self.async_session() as session:
            result = await session.execute(
                select(URL).where(
                    and_(URL.short_code == short_code, URL.is_active == True)
                )
            )
            return result.scalar_one_or_none()

    async def get_by_original_url(self, original_url: str) -> Optional[URL]:
        """Check if original URL already exists"""
        async with self.async_session() as session:
            result = await session.execute(
                select(URL).where(
                    and_(URL.original_url == original_url, URL.is_active == True)
                )
            )
            return result.scalar_one_or_none()

    async def create_url(self, original_url: str, custom_alias: Optional[str], ip: str) -> URL:
        """Create new URL mapping"""
        async with self.async_session() as session:

            short_code= "temp"
            if custom_alias:
                short_code=custom_alias

            url = URL(
                short_code=short_code,
                original_url=original_url,
                created_by_ip=ip
            )
            session.add(url)
            await session.flush()
            await session.commit()
            await session.refresh(url)
            return url

    async def update_short_code(self, xid: int, short_code: str) -> None:
        """Update short code after ID generation"""
        async with self.async_session() as session:
            await session.execute(
                update(URL).where(URL.id == xid).values(short_code=short_code)
            )
            await session.commit()

    async def increment_click_count(self, short_code: str) -> None:
        """Increment click count and update last accessed time"""
        async with self.async_session() as session:
            await session.execute(
                update(URL)
                .where(URL.short_code == short_code)
                .values(
                    click_count=URL.click_count + 1,
                    last_accessed_at=datetime.now()
                )
            )
            await session.commit()

    async def get_paginated_urls(self, page: int, page_size: int) -> tuple[Sequence[URL], Optional[Any]]:
        """Get paginated list of URLs"""
        async with self.async_session() as session:
            # Get total count
            count_result = await session.execute(select(func.count(URL.id)))
            total = count_result.scalar()

            # Get paginated results
            result = await session.execute(
                select(URL)
                .order_by(URL.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            urls = result.scalars().all()
            return urls, total

    async def get_analytics(self) -> dict:
        """Get analytics data"""
        async with self.async_session() as session:
            # Total URLs
            total_urls = await session.execute(select(func.count(URL.id)))

            # Total clicks
            total_clicks = await session.execute(select(func.sum(URL.click_count)))

            # Active URLs
            active_urls = await session.execute(
                select(func.count(URL.id)).where(URL.is_active)
            )

            # Clicks today
            today = datetime.now().date()
            clicks_today = await session.execute(
                select(func.sum(URL.click_count))
                .where(URL.last_accessed_at >= today)
            )

            return {
                "total_urls": total_urls.scalar() or 0,
                "total_clicks": total_clicks.scalar() or 0,
                "active_urls": active_urls.scalar() or 0,
                "clicks_today": clicks_today.scalar() or 0
            }

    async def delete_url(self, short_code: str) -> bool:
        """Soft delete URL"""
        async with self.async_session() as session:
            result = await session.execute(
                update(URL)
                .where(URL.short_code == short_code)
                .values(is_active=False)
            )
            await session.commit()
            return result.rowcount > 0  # type: ignore[attr-defined]

url_repository = URLRepository()
