"""
CLARA Dataset Management Backend - FastAPI Application

Microservice für Dataset-Vorbereitung und -Verwaltung
Port: 45681
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import config
from .manager import DatasetManager, UDS3_AVAILABLE
from .api import routes

# Logging Setup
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from centralized config
SERVICE_NAME = "clara_dataset_backend"
SERVICE_PORT = config.dataset_port

# Global manager
dataset_manager: Optional[DatasetManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan für Startup/Shutdown"""
    global dataset_manager
    
    # Startup
    logger.info("🚀 Dataset Backend startet...")
    
    dataset_manager = DatasetManager()
    
    # Inject into routes
    routes.dataset_manager = dataset_manager
    
    logger.info(f"✅ Dataset Backend bereit (Port {SERVICE_PORT})")
    
    # Yield control
    yield
    
    # Shutdown
    logger.info("🛑 Dataset Backend wird gestoppt...")
    logger.info("✅ Shutdown abgeschlossen")


# Create FastAPI app
app = FastAPI(
    title="CLARA Dataset Management Backend",
    description="Microservice für Dataset-Vorbereitung und -Verwaltung",
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
            "datasets": "/api/datasets",
            "create_dataset": "/api/datasets (POST)"
        }
    }


@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "port": SERVICE_PORT,
        "uds3_available": UDS3_AVAILABLE,
        "datasets_count": len(dataset_manager.datasets) if dataset_manager else 0,
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("CLARA Dataset Management Backend")
    logger.info("=" * 60)
    logger.info(f"Port: {SERVICE_PORT}")
    logger.info(f"UDS3 Available: {UDS3_AVAILABLE}")
    logger.info("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        log_level="info"
    )
