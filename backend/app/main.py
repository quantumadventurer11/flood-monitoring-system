"""
Flood Monitoring System - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .config import settings
from .database import engine, Base, init_db
from .api.routes import auth, geographic, sensors, alerts, events, ingestion

# Import all models to ensure they're registered with Base
from .models import auth as auth_models
from .models import geographic as geographic_models
from .models import sensors as sensors_models
from .models import ingestion as ingestion_models
from .models import modeling as modeling_models
from .models import events as events_models
from .models import alerts as alerts_models
from .models import audit as audit_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: Initialize database with PostGIS
    init_db()
    # Create tables (for development; use migrations in production)
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown cleanup if needed
    pass


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Flood Monitoring System with satellite data integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(geographic.router, prefix=f"{settings.API_V1_PREFIX}/geographic", tags=["Geographic"])
app.include_router(sensors.router, prefix=f"{settings.API_V1_PREFIX}/sensors", tags=["Sensors"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_PREFIX}/alerts", tags=["Alerts"])
app.include_router(events.router, prefix=f"{settings.API_V1_PREFIX}/events", tags=["Flood Events"])
app.include_router(ingestion.router, prefix=f"{settings.API_V1_PREFIX}/ingestion", tags=["Data Ingestion"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "AI-Powered Flood Monitoring System",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "flood-monitoring-api"}