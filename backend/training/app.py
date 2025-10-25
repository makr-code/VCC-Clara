"""
CLARA Training Backend - FastAPI Application

Microservice für LoRA/QLoRA Training Management
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from .manager import TrainingJobManager
from .api import routes

# Logging Setup
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from centralized config
SERVICE_NAME = "clara_training_backend"
SERVICE_PORT = config.training_port
MAX_CONCURRENT_JOBS = config.max_concurrent_jobs

# Global manager
job_manager: Optional[TrainingJobManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan für Startup/Shutdown"""
    global job_manager
    
    # Startup
    logger.info("🚀 Training Backend startet...")
    
    job_manager = TrainingJobManager(max_concurrent_jobs=MAX_CONCURRENT_JOBS)
    await job_manager.start_workers()
    
    # Inject into routes
    routes.job_manager = job_manager
    
    logger.info(f"✅ Training Backend bereit (Port {SERVICE_PORT})")
    
    # Yield control
    yield
    
    # Shutdown
    logger.info("🛑 Training Backend wird gestoppt...")
    await job_manager.stop_workers()
    logger.info("✅ Shutdown abgeschlossen")


# Create FastAPI app
app = FastAPI(
    title="CLARA Training Backend",
    description="Microservice für LoRA/QLoRA Training Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Production - spezifischer setzen
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router)


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "training_jobs": "/api/training/jobs",
            "websocket": "/api/training/ws"
        }
    }


@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    from datetime import datetime
    
    active_jobs = len(job_manager._get_active_jobs()) if job_manager else 0
    
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "port": SERVICE_PORT,
        "active_jobs": active_jobs,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Start FastAPI Server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        log_level="info"
    )
