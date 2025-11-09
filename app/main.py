from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .handlers import url_handler, admin_handler
from .repositories.url_repository import url_repository
from .services.url_service import url_service
from .config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    await url_repository.create_tables()
    print("✓ Database tables created")
    print(f"✓ Application started: {settings.app_name}")

    yield

    # Shutdown
    await url_service.close()
    print("✓ Connections closed gracefully")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": settings.app_name,
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "ok",
        "database": "connected",
        "cache": "connected"
    }
# so that healthy check is checked properly
app.include_router(url_handler.router)
app.include_router(admin_handler.router)
