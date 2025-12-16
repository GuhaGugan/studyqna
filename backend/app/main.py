from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.routers import auth, upload, qna, user, admin, reviews, ai_usage
import asyncio
import sys
import logging

# Configure logging to suppress Windows-specific asyncio network errors
# These are non-critical errors that occur when clients disconnect abruptly
if sys.platform == 'win32':
    # Create a custom filter for Windows network errors
    class WindowsNetworkErrorFilter(logging.Filter):
        def filter(self, record):
            # Suppress "The specified network name is no longer available" errors
            if hasattr(record, 'msg') and isinstance(record.msg, str):
                if 'WinError 64' in record.msg or 'network name is no longer available' in record.msg:
                    return False
                if 'Accept failed on a socket' in record.msg:
                    return False
            if hasattr(record, 'exc_info') and record.exc_info:
                exc_type, exc_value, exc_traceback = record.exc_info
                if isinstance(exc_value, OSError):
                    if hasattr(exc_value, 'winerror') and exc_value.winerror == 64:
                        return False
                    if hasattr(exc_value, 'errno') and exc_value.errno == 64:
                        return False
            return True
    
    # Apply filter to asyncio logger
    asyncio_logger = logging.getLogger('asyncio')
    asyncio_logger.addFilter(WindowsNetworkErrorFilter())

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    print("🚀 Starting StudyQnA Generator API...")
    
    # Initialize fonts on startup
    try:
        from app.font_manager import initialize_fonts
        initialize_fonts()
        print("✅ Fonts initialized")
    except Exception as e:
        print(f"⚠️  Font initialization warning: {e}")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down StudyQnA Generator API...")
    
    # Close database connections first
    try:
        engine.dispose()
        print("✅ Database connections closed")
    except Exception as e:
        print(f"⚠️  Error closing database connections: {e}")
    
    # Note: Let asyncio handle task cancellation automatically during shutdown
    # Attempting to manually cancel tasks can cause recursion issues
    print("✅ Application shutdown complete")

app = FastAPI(
    title=settings.APP_NAME,
    description="StudyQnA Generator - AI-powered Q/A generation from PDFs and Images",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(qna.router, prefix="/api/qna", tags=["QnA"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["Reviews"])
app.include_router(ai_usage.router, prefix="/api/admin/ai", tags=["AI Usage"])

@app.get("/")
async def root():
    return {"message": "StudyQnA Generator API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

