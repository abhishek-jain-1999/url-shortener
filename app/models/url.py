from sqlalchemy import Column, String, Integer, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class URL(Base):
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_code = Column(String(10), unique=True, nullable=False, index=True)
    original_url = Column(String(2048), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    click_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    created_by_ip = Column(String(45), nullable=True)

    __table_args__ = (
        Index('idx_original_url_hash', 'original_url', postgresql_using='hash'),
        Index('idx_created_at', 'created_at'),
        Index('idx_short_code', 'short_code', postgresql_using='hash'),
    )
