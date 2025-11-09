from pydantic_settings import BaseSettings
from functools import lru_cache
from urllib.parse import quote_plus

class Settings(BaseSettings):
    # Application
    app_name: str = "URL Shortener"
    env_name: str = "development"
    base_url: str = "http://localhost:8080"

    # Database
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "url_shortener"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_ttl: int = 86400  # 24 hours

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # URL Settings
    short_code_length: int = 10
    url_retention_days: int = 1825  # 5 years

    # Admin Auth
    admin_token: str = "change-this-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        encoded_password = quote_plus(self.postgres_password)
        return f"postgresql://{self.postgres_user}:{encoded_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
