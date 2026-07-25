"""Main FastAPI Backend Application Entry Point.

Rule 1.2: All backend API routes use /api/* prefix.
Rule 1.12: Configuration encapsulated in config module.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, SessionLocal
from app.services.pipeline import run_etl_pipeline
from app.utils.logger import log_info, log_error

# Import Routers
from app.routes.health import router as health_router
from app.routes.events import router as events_router
from app.routes.map import router as map_router
from app.routes.dashboard import router as dashboard_router
from app.routes.communities import router as communities_router
from app.routes.categories import router as categories_router
from app.routes.quality import router as quality_router


@asynccontextmanager
async def lifespan(app_instance: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan async context manager for app startup and shutdown events."""
    try:
        log_info("lifespan", "Initializing database tables on startup")
        init_db()

        # Seed sample data if database table is empty
        db = SessionLocal()
        try:
            from app.models.domain import Event
            event_count = db.query(Event).count()
            if event_count == 0:
                raw_csv = "data/raw/Week3_Task_3_raw_event_sample.csv"
                proc_csv = "data/processed/Week3_Task_3_standardised_event_sample.csv"
                val_log = "data/validation_logs/Week3_Task_3_data_quality_validation_log.csv"
                log_info("lifespan", "Database empty. Running sample data ingestion pipeline.")
                run_etl_pipeline(raw_csv, proc_csv, val_log, db)
        finally:
            db.close()
    except Exception as e:
        log_error("lifespan", "Startup database initialization encountered an issue", error=e)
    
    yield
    log_info("lifespan", "Application shutting down")


app = FastAPI(
    title=settings.app_name,
    description="Community-Driven Tourism & Entertainment Discovery Portal API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for frontend client calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(health_router)
app.include_router(events_router)
app.include_router(map_router)
app.include_router(dashboard_router)
app.include_router(communities_router)
app.include_router(categories_router)
app.include_router(quality_router)
