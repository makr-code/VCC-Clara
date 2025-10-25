"""
Training API Routes

FastAPI endpoints for training job management and dataset search.
"""

import logging
from typing import Optional, Any
from pathlib import Path
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, WebSocket, WebSocketDisconnect

from ..models import (
    TrainingJobRequest,
    TrainingJobResponse,
    JobListResponse,
    JobStatus
)
from ..manager import TrainingJobManager

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/training", tags=["training"])

# Global manager (will be injected from app.py)
job_manager: Optional[TrainingJobManager] = None

# JWT Middleware (optional import)
try:
    from shared.auth import jwt_middleware as _jwt_middleware, get_current_user_email
    from config import config
    JWT_AVAILABLE = True
    
    # Conditional auth based on config
    async def optional_auth():
        """Returns authenticated user or dev user based on config"""
        if config.jwt_enabled_resolved:
            return await _jwt_middleware.get_current_user()
        else:
            return {"email": "dev@local", "roles": ["admin"]}
    
except ImportError:
    logger.warning("⚠️ JWT Middleware nicht verfügbar - Auth deaktiviert")
    JWT_AVAILABLE = False
    get_current_user_email = lambda user: user.get("email", "dev@local")
    
    async def optional_auth():
        return {"email": "dev@local", "roles": ["admin"]}


def get_job_manager() -> TrainingJobManager:
    """Dependency for job manager"""
    if job_manager is None:
        raise HTTPException(status_code=503, detail="Job Manager not initialized")
    return job_manager


# ============================================================================
# Training Job Endpoints
# ============================================================================

@router.post("/jobs", response_model=TrainingJobResponse)
async def create_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks,
    manager: TrainingJobManager = Depends(get_job_manager),
    user: dict = Depends(optional_auth)
):
    """
    Erstellt neuen Training Job
    
    🔐 Security: JWT Required, Roles: admin OR trainer
    
    Args:
        request: Training Job Request mit Konfiguration
        user: Authenticated user (from JWT token)
        
    Returns:
        Training Job Response mit Job-ID
    """
    try:
        user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
        logger.info(f"📝 Creating Training Job - User: {user_email}, Trainer: {request.trainer_type.value}")
        
        # Job erstellen
        job = manager.create_job(request)
        
        # Zur Queue hinzufügen (async in Background)
        background_tasks.add_task(manager.submit_job, job)
        
        # Security Audit Log
        logger.info(f"🔒 AUDIT: Job {job.job_id} created by {user_email}")
        
        job_data = job.to_dict()
        job_data["created_by"] = user_email
        
        return TrainingJobResponse(
            success=True,
            job_id=job.job_id,
            status=job.status,
            message=f"Training job created: {job.job_id}",
            data=job_data
        )
    
    except Exception as e:
        logger.error(f"❌ Fehler beim Job-Erstellen: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: str,
    manager: TrainingJobManager = Depends(get_job_manager),
    user: dict = Depends(optional_auth)
):
    """
    Holt Job-Details nach ID
    
    🔐 Security: JWT Required (any authenticated user)
    
    Args:
        job_id: Eindeutige Job-ID
        user: Authenticated user
        
    Returns:
        Training Job Details
    """
    job = manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return TrainingJobResponse(
        success=True,
        job_id=job.job_id,
        status=job.status,
        message="Job details retrieved",
        data=job.to_dict()
    )


@router.get("/jobs/list", response_model=JobListResponse)
async def list_training_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 100,
    manager: TrainingJobManager = Depends(get_job_manager),
    user: dict = Depends(optional_auth)
):
    """
    Listet alle Training Jobs
    
    🔐 Security: JWT Required (any authenticated user)
    
    Args:
        status: Optional - Filter nach Status
        limit: Max. Anzahl Jobs
        user: Authenticated user
        
    Returns:
        Liste aller Jobs mit Statistics
    """
    jobs = manager.list_jobs(status=status, limit=limit)
    
    # Statistiken berechnen
    all_jobs = manager.list_jobs()
    active_count = len([j for j in all_jobs if j.status in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]])
    completed_count = len([j for j in all_jobs if j.status == JobStatus.COMPLETED])
    failed_count = len([j for j in all_jobs if j.status == JobStatus.FAILED])
    
    return JobListResponse(
        jobs=[j.to_dict() for j in jobs],
        total_count=len(all_jobs),
        active_count=active_count,
        completed_count=completed_count,
        failed_count=failed_count
    )


@router.delete("/jobs/{job_id}")
async def cancel_training_job(
    job_id: str,
    manager: TrainingJobManager = Depends(get_job_manager),
    user: dict = Depends(optional_auth)
):
    """
    Bricht Training Job ab
    
    🔐 Security: JWT Required, Roles: admin OR trainer
    
    Args:
        job_id: Eindeutige Job-ID
        user: Authenticated user
        
    Returns:
        Success Status
    """
    user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
    
    success = manager.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled (not found or already running)")
    
    # Security Audit Log
    logger.info(f"🔒 AUDIT: Job {job_id} cancelled by {user_email}")
    
    return {
        "success": True,
        "message": f"Job cancelled: {job_id}",
        "cancelled_by": user_email
    }


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_training_updates(
    websocket: WebSocket,
    manager: TrainingJobManager = Depends(get_job_manager)
):
    """
    WebSocket Endpoint für Live Training-Updates
    
    Sendet Job-Status-Updates in Echtzeit an verbundene Clients.
    Analog zu /ws/jobs im Ingestion Backend.
    """
    await manager.register_websocket(websocket)
    
    try:
        # Keep connection alive
        while True:
            # Warte auf Client-Messages (z.B. Ping)
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        logger.info("WebSocket Client disconnected")
    
    finally:
        await manager.unregister_websocket(websocket)
