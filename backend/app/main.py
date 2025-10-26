from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routes import auth_router, matches_router, stats_router, sync_router, heroes_router
from .config import settings
from .logging_config import setup_logging
import logging

# Setup logging
setup_logging("/app/logs/error.log")
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="Dota 2 statistics tracking API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(matches_router)
app.include_router(stats_router)
app.include_router(sync_router)
app.include_router(heroes_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Dota Stats API...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
