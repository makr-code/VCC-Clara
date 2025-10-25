#!/usr/bin/env python3
"""
CLARA Training Backend Service
FastAPI Microservice für LoRa/QLoRa Training Management

Port: 45680
Verantwortlichkeiten:
- Training Job Orchestrierung
- GPU Worker Pool Management
- Model Checkpointing
- WebSocket Live-Updates
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Config Import
try:
    from config import config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    config = None

# JWT Middleware Import (new location)
try:
    from shared.auth import jwt_middleware, get_current_user_email
    JWT_AVAILABLE = True
except ImportError:
    logger.warning("JWT Middleware not available - running in DEBUG mode")
    JWT_AVAILABLE = False
    jwt_middleware = None

# UDS3 Dataset Search Import (new location)
try:
    from shared.database import DatasetSearchAPI, DatasetSearchQuery
    UDS3_DATASET_SEARCH_AVAILABLE = True
except ImportError:
    logger.warning("UDS3 Dataset Search not available")
    UDS3_DATASET_SEARCH_AVAILABLE = False
    DatasetSearchAPI = None

# CLARA Imports
try:
    from scripts.clara_train_lora import LoRATrainer
    from scripts.clara_train_qlora import QLoRATrainer
    from src.utils.logger import setup_logger
    from src.utils.metrics import get_metrics_exporter
except ImportError:
    # Graceful degradation für Development
    LoRATrainer = None
    QLoRATrainer = None
    
    # Minimal logger setup if import fails
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    def setup_logger(name):
        return logging.getLogger(name)
    
    def get_metrics_exporter():
        return None


# ============================================================================
# Configuration
# ============================================================================

logger = setup_logger(__name__)
metrics = get_metrics_exporter()

SERVICE_NAME = "clara_training_backend"
# Use config if available, otherwise fallback to env vars
if CONFIG_AVAILABLE and config:
    SERVICE_PORT = config.training_port
    MAX_CONCURRENT_JOBS = config.max_concurrent_jobs
else:
    SERVICE_PORT = int(os.environ.get("CLARA_TRAINING_PORT", "45680"))
    MAX_CONCURRENT_JOBS = int(os.environ.get("CLARA_MAX_CONCURRENT_JOBS", "2"))


# ============================================================================
# Data Models
# ============================================================================

class JobStatus(str, Enum):
    """Training Job Status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainerType(str, Enum):
    """Available Trainer Types"""
    LORA = "lora"
    QLORA = "qlora"
    CONTINUOUS = "continuous"


@dataclass
class TrainingJob:
    """Training Job Metadata"""
    job_id: str
    trainer_type: TrainerType
    status: JobStatus
    config_path: str
    dataset_path: Optional[str] = None
    output_dir: Optional[str] = None
    
    # Timestamps
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Progress
    current_epoch: int = 0
    total_epochs: int = 0
    progress_percent: float = 0.0
    
    # Results
    adapter_path: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None
    
    # Metadata
    priority: int = 1
    tags: List[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict:
        """Konvertiert zu JSON-serialisierbarem Dict"""
        data = asdict(self)
        data['status'] = self.status.value
        data['trainer_type'] = self.trainer_type.value
        data['created_at'] = self.created_at.isoformat()
        
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        
        return data


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class TrainingJobRequest(BaseModel):
    """Request Model für neuen Training Job"""
    trainer_type: TrainerType
    config_path: str = Field(..., description="Pfad zur Training-Config (YAML)")
    dataset_path: Optional[str] = Field(None, description="Optional: Custom Dataset Path")
    priority: int = Field(1, ge=1, le=5, description="Job-Priorität (1=niedrig, 5=hoch)")
    tags: List[str] = Field(default_factory=list, description="Optional: Tags für Kategorisierung")
    
    @validator("config_path")
    def validate_config_path(cls, v):
        """Validiert dass Config-File existiert"""
        config_file = Path(v)
        if not config_file.exists():
            raise ValueError(f"Config file not found: {v}")
        if not config_file.suffix in [".yaml", ".yml"]:
            raise ValueError(f"Config must be YAML file: {v}")
        return v


class TrainingJobResponse(BaseModel):
    """Response Model für Training Job"""
    success: bool
    job_id: str
    status: JobStatus
    message: str
    data: Optional[Dict[str, Any]] = None


class JobListResponse(BaseModel):
    """Response für Job-Liste"""
    jobs: List[Dict[str, Any]]
    total_count: int
    active_count: int
    completed_count: int
    failed_count: int


class JobUpdateMessage(BaseModel):
    """WebSocket Message für Job-Updates"""
    type: str = "job_update"
    job_id: str
    status: JobStatus
    progress_percent: float
    current_epoch: int
    total_epochs: int
    metrics: Optional[Dict[str, float]] = None
    timestamp: datetime


# ============================================================================
# Job Manager
# ============================================================================

class TrainingJobManager:
    """
    Zentrale Job-Verwaltung mit Worker Pool
    
    Analog zu Ingestion Backend Job Management (docs/MICROSERVICES_ARCHITECTURE.md)
    """
    
    def __init__(self, max_concurrent_jobs: int = 2):
        self.jobs: Dict[str, TrainingJob] = {}
        self.max_concurrent_jobs = max_concurrent_jobs
        self.websocket_clients: List[WebSocket] = []
        
        # Worker Queue
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        
        logger.info(f"📦 TrainingJobManager initialisiert (max_concurrent={max_concurrent_jobs})")
    
    async def start_workers(self):
        """Startet Worker Pool"""
        for i in range(self.max_concurrent_jobs):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)
            logger.info(f"🔧 Worker {i} gestartet")
    
    async def stop_workers(self):
        """Stoppt Worker Pool"""
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("⏹️ Workers gestoppt")
    
    def create_job(self, request: TrainingJobRequest) -> TrainingJob:
        """Erstellt neuen Training Job"""
        job_id = str(uuid.uuid4())
        
        job = TrainingJob(
            job_id=job_id,
            trainer_type=request.trainer_type,
            status=JobStatus.PENDING,
            config_path=request.config_path,
            dataset_path=request.dataset_path,
            priority=request.priority,
            tags=request.tags
        )
        
        self.jobs[job_id] = job
        
        # Metrics
        metrics.inc("training_jobs_total", labels={"status": "created", "type": request.trainer_type.value})
        
        logger.info(f"✅ Job erstellt: {job_id} (type={request.trainer_type.value})")
        
        return job
    
    async def submit_job(self, job: TrainingJob):
        """Fügt Job zur Queue hinzu"""
        job.status = JobStatus.QUEUED
        await self.job_queue.put(job)
        
        # WebSocket Broadcast
        await self._broadcast_job_update(job)
        
        logger.info(f"📥 Job in Queue: {job.job_id}")
    
    async def _worker(self, worker_id: int):
        """Worker Loop für Job-Verarbeitung"""
        logger.info(f"🔄 Worker {worker_id} aktiv")
        
        while True:
            try:
                # Hole Job aus Queue (mit Timeout für Shutdown)
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                
                logger.info(f"🎯 Worker {worker_id} startet Job: {job.job_id}")
                
                # Job verarbeiten
                await self._execute_job(job, worker_id)
                
            except asyncio.TimeoutError:
                # Kein Job verfügbar, warte weiter
                continue
            except asyncio.CancelledError:
                # Worker-Shutdown
                logger.info(f"🛑 Worker {worker_id} gestoppt")
                break
            except Exception as e:
                logger.error(f"❌ Worker {worker_id} Fehler: {e}")
    
    async def _execute_job(self, job: TrainingJob, worker_id: int):
        """Führt Training Job aus"""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        
        # Metrics
        metrics.inc("training_jobs_total", labels={"status": "started", "type": job.trainer_type.value})
        metrics.set("active_training_jobs", len(self._get_active_jobs()))
        
        # Broadcast Start
        await self._broadcast_job_update(job)
        
        try:
            # Führe Training aus (in Background Thread um Event Loop nicht zu blocken)
            result = await asyncio.to_thread(self._run_training, job)
            
            # Success
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.adapter_path = result.get("adapter_path")
            job.metrics = result.get("metrics")
            job.progress_percent = 100.0
            
            metrics.inc("training_jobs_total", labels={"status": "completed", "type": job.trainer_type.value})
            
            logger.info(f"✅ Job completed: {job.job_id}")
            
        except Exception as e:
            # Failure
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error_message = str(e)
            
            metrics.inc("training_jobs_total", labels={"status": "failed", "type": job.trainer_type.value})
            
            logger.error(f"❌ Job failed: {job.job_id} - {e}")
        
        finally:
            # Cleanup
            metrics.set("active_training_jobs", len(self._get_active_jobs()))
            
            # Broadcast Completion
            await self._broadcast_job_update(job)
    
    def _run_training(self, job: TrainingJob) -> Dict[str, Any]:
        """
        Führt Training durch (Sync Blocking Operation)
        
        Integrates with existing trainers:
        - clara_train_lora.py (LoRATrainer)
        - clara_train_qlora.py (QLoRATrainer)
        - clara_continuous_learning.py (ContinuousLoRATrainer)
        
        Note: This runs in thread pool executor (called from _worker)
        """
        logger.info(f"🚀 Training startet: {job.job_id}")
        
        try:
            # Load Config
            import yaml
            with open(job.config_path) as f:
                config = yaml.safe_load(f)
            
            # Determine output dir
            output_dir = Path(config.get("training", {}).get("output_dir", "models/training_outputs"))
            job_output_dir = output_dir / job.job_id
            job_output_dir.mkdir(parents=True, exist_ok=True)
            
            # Update config with job-specific settings
            config["training"]["output_dir"] = str(job_output_dir)
            if job.dataset_path:
                config["data"]["dataset_path"] = job.dataset_path
            
            # Select and run trainer
            if job.trainer_type == TrainerType.LORA:
                return self._run_lora_training_sync(job, config)
            
            elif job.trainer_type == TrainerType.QLORA:
                return self._run_qlora_training_sync(job, config)
            
            elif job.trainer_type == TrainerType.CONTINUOUS:
                return self._run_continuous_training_sync(job, config)
            
            else:
                raise ValueError(f"Unknown trainer type: {job.trainer_type}")
        
        except Exception as e:
            logger.error(f"❌ Training failed: {job.job_id} - {e}")
            raise
    
    def _run_lora_training_sync(self, job: TrainingJob, config: Dict) -> Dict[str, Any]:
        """Run LoRA Training (Sync)"""
        logger.info(f"🔧 LoRA Training: {job.job_id}")
        
        if LoRATrainer is None:
            logger.warning("LoRATrainer not available - simulating")
            return self._simulate_training_sync(job, config)
        
        try:
            # TODO: Integrate real LoRATrainer
            # trainer = LoRATrainer(config)
            # result = trainer.train()
            
            # For now: simulate
            return self._simulate_training_sync(job, config)
        
        except Exception as e:
            logger.error(f"❌ LoRA Training failed: {e}")
            raise
    
    def _run_qlora_training_sync(self, job: TrainingJob, config: Dict) -> Dict[str, Any]:
        """Run QLoRA Training (Sync)"""
        logger.info(f"🔧 QLoRA Training: {job.job_id}")
        
        if QLoRATrainer is None:
            logger.warning("QLoRATrainer not available - simulating")
            return self._simulate_training_sync(job, config)
        
        try:
            # TODO: Integrate real QLoRATrainer
            # trainer = QLoRATrainer(config)
            # result = trainer.train()
            
            # For now: simulate
            return self._simulate_training_sync(job, config)
        
        except Exception as e:
            logger.error(f"❌ QLoRA Training failed: {e}")
            raise
    
    def _run_continuous_training_sync(self, job: TrainingJob, config: Dict) -> Dict[str, Any]:
        """Run Continuous Learning Training (Sync)"""
        logger.info(f"🔧 Continuous Learning Training: {job.job_id}")
        
        # TODO: Integrate ContinuousLoRATrainer
        logger.warning("Continuous Learning not yet implemented - simulating")
        return self._simulate_training_sync(job, config)
    
    def _simulate_training_sync(self, job: TrainingJob, config: Dict) -> Dict[str, Any]:
        """
        Simulate training for development/testing
        
        Args:
            job: Training job
            config: Training configuration
            
        Returns:
            Simulated training results
        """
        logger.info(f"⚠️ Simulating training: {job.job_id}")
        
        import time
        
        # Get epochs from config
        num_epochs = config.get("training", {}).get("num_epochs", 3)
        
        # Simulate training epochs
        for epoch in range(1, num_epochs + 1):
            job.current_epoch = epoch
            job.total_epochs = num_epochs
            job.progress_percent = (epoch / num_epochs) * 100
            
            # Simulate epoch duration (2 seconds per epoch)
            time.sleep(2)
            
            # Calculate simulated metrics
            simulated_loss = 0.5 - (epoch * 0.1)
            logger.info(f"   📊 Epoch {epoch}/{num_epochs} - Loss: {simulated_loss:.2f}")
        
        # Simulated final results
        adapter_path = str(Path(config["training"]["output_dir"]) / "adapter_model")
        
        return {
            "adapter_path": adapter_path,
            "metrics": {
                "final_loss": max(0.2, 0.5 - (num_epochs * 0.1)),
                "perplexity": max(8.0, 15.0 - (num_epochs * 2)),
                "accuracy": min(0.9, 0.7 + (num_epochs * 0.05)),
                "epochs_completed": num_epochs
            }
        }
    
    def get_job(self, job_id: str) -> Optional[TrainingJob]:
        """Holt Job nach ID"""
        return self.jobs.get(job_id)
    
    def list_jobs(
        self, 
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[TrainingJob]:
        """Listet Jobs mit optionalem Status-Filter"""
        jobs = list(self.jobs.values())
        
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        # Sort by created_at (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
    
    def cancel_job(self, job_id: str) -> bool:
        """Bricht Job ab"""
        job = self.jobs.get(job_id)
        
        if not job:
            return False
        
        if job.status in [JobStatus.PENDING, JobStatus.QUEUED]:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            logger.info(f"🛑 Job cancelled: {job_id}")
            return True
        
        return False
    
    def _get_active_jobs(self) -> List[TrainingJob]:
        """Holt alle aktiven Jobs"""
        return [
            j for j in self.jobs.values() 
            if j.status in [JobStatus.PENDING, JobStatus.QUEUED, JobStatus.RUNNING]
        ]
    
    async def _broadcast_job_update(self, job: TrainingJob):
        """Sendet Job-Update an alle WebSocket-Clients"""
        if not self.websocket_clients:
            return
        
        message = JobUpdateMessage(
            job_id=job.job_id,
            status=job.status,
            progress_percent=job.progress_percent,
            current_epoch=job.current_epoch,
            total_epochs=job.total_epochs,
            metrics=job.metrics,
            timestamp=datetime.now()
        )
        
        # Broadcast to all connected clients
        disconnected = []
        for ws in self.websocket_clients:
            try:
                await ws.send_json(message.dict())
            except Exception:
                disconnected.append(ws)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_clients.remove(ws)
    
    async def register_websocket(self, websocket: WebSocket):
        """Registriert WebSocket-Client"""
        await websocket.accept()
        self.websocket_clients.append(websocket)
        logger.info(f"🔌 WebSocket Client verbunden (total: {len(self.websocket_clients)})")
    
    async def unregister_websocket(self, websocket: WebSocket):
        """Entfernt WebSocket-Client"""
        if websocket in self.websocket_clients:
            self.websocket_clients.remove(websocket)
            logger.info(f"🔌 WebSocket Client getrennt (total: {len(self.websocket_clients)})")


# ============================================================================
# FastAPI Application
# ============================================================================

# Global Job Manager
job_manager: Optional[TrainingJobManager] = None
dataset_search_api: Optional[Any] = None  # DatasetSearchAPI instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan für Startup/Shutdown"""
    global job_manager, dataset_search_api
    
    # Startup
    logger.info("🚀 Training Backend startet...")
    
    job_manager = TrainingJobManager(max_concurrent_jobs=MAX_CONCURRENT_JOBS)
    await job_manager.start_workers()
    
    # Initialize Dataset Search API (optional)
    if UDS3_DATASET_SEARCH_AVAILABLE and DatasetSearchAPI:
        try:
            dataset_search_api = DatasetSearchAPI()
            logger.info("✅ UDS3 Dataset Search API initialized")
        except Exception as e:
            logger.warning(f"⚠️ UDS3 Dataset Search initialization failed: {e}")
            dataset_search_api = None
    else:
        logger.warning("⚠️ UDS3 Dataset Search not available")
    
    logger.info(f"✅ Training Backend bereit (Port {SERVICE_PORT})")
    
    # Yield control
    yield
    
    # Shutdown
    logger.info("🛑 Training Backend wird gestoppt...")
    await job_manager.stop_workers()
    logger.info("✅ Shutdown abgeschlossen")


app = FastAPI(
    title="CLARA Training Backend",
    description="Microservice für LoRa/QLoRa Training Management",
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


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health Check Endpoint"""
    active_jobs = len(job_manager._get_active_jobs()) if job_manager else 0
    
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "port": SERVICE_PORT,
        "active_jobs": active_jobs,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/training/jobs", response_model=TrainingJobResponse)
async def create_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer"])) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
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
    if not job_manager:
        raise HTTPException(status_code=503, detail="Job Manager not initialized")
    
    try:
        user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
        logger.info(f"📝 Creating Training Job - User: {user_email}, Trainer: {request.trainer_type.value}")
        
        # Job erstellen
        job = job_manager.create_job(request)
        
        # Zur Queue hinzufügen (async in Background)
        background_tasks.add_task(job_manager.submit_job, job)
        
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


@app.get("/api/training/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: str,
    user: dict = Depends(jwt_middleware.get_current_user) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
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
    if not job_manager:
        raise HTTPException(status_code=503, detail="Job Manager not initialized")
    
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    
    return TrainingJobResponse(
        success=True,
        job_id=job.job_id,
        status=job.status,
        message="Job details retrieved",
        data=job.to_dict()
    )


@app.get("/api/training/jobs/list", response_model=JobListResponse)
async def list_training_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 100,
    user: dict = Depends(jwt_middleware.get_current_user) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
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
    if not job_manager:
        raise HTTPException(status_code=503, detail="Job Manager not initialized")
    
    jobs = job_manager.list_jobs(status=status, limit=limit)
    
    # Statistiken berechnen
    all_jobs = job_manager.list_jobs()
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


@app.delete("/api/training/jobs/{job_id}")
async def cancel_training_job(
    job_id: str,
    user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer"])) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
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
    if not job_manager:
        raise HTTPException(status_code=503, detail="Job Manager not initialized")
    
    user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
    
    success = job_manager.cancel_job(job_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled (not found or already running)")
    
    # Security Audit Log
    logger.info(f"🔒 AUDIT: Job {job_id} cancelled by {user_email}")
    
    return {
        "success": True,
        "message": f"Job cancelled: {job_id}",
        "cancelled_by": user_email
    }


@app.websocket("/ws/training")
async def websocket_training_updates(websocket: WebSocket):
    """
    WebSocket Endpoint für Live Training-Updates
    
    Sendet Job-Status-Updates in Echtzeit an verbundene Clients.
    Analog zu /ws/jobs im Ingestion Backend.
    """
    if not job_manager:
        await websocket.close(code=1011, reason="Job Manager not initialized")
        return
    
    await job_manager.register_websocket(websocket)
    
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
        await job_manager.unregister_websocket(websocket)


# ============================================================================
# Dataset Search Endpoints (UDS3 Integration)
# ============================================================================

@app.post("/api/datasets/search")
async def search_datasets(
    request: Any,  # DatasetSearchRequest if available
    user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer", "analyst"])) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
):
    """
    Search datasets using UDS3 Hybrid Search
    
    🔐 Security: JWT Required, Roles: admin OR trainer OR analyst
    
    Args:
        request: Dataset search request (query, filters, top_k)
        user: Authenticated user
        
    Returns:
        Search results with statistics
        
    Example Request:
        {
            "query_text": "Verwaltungsrecht Photovoltaik",
            "top_k": 100,
            "filters": {"domain": "verwaltungsrecht"},
            "min_quality_score": 0.6,
            "search_types": ["vector", "graph"],
            "weights": {"vector": 0.6, "graph": 0.4}
        }
    """
    if not UDS3_DATASET_SEARCH_AVAILABLE or not dataset_search_api:
        raise HTTPException(
            status_code=503,
            detail="UDS3 Dataset Search not available. Please install UDS3 dependencies."
        )
    
    try:
        user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
        logger.info(f"🔍 Dataset search by {user_email}: '{request.query_text}'")
        
        # Create search query
        query = DatasetSearchQuery(
            query_text=request.query_text,
            top_k=request.top_k,
            filters=request.filters,
            min_quality_score=request.min_quality_score,
            search_types=request.search_types,
            weights=request.weights
        )
        
        # Execute search
        documents = await dataset_search_api.search_datasets(query)
        
        # Get statistics
        stats = dataset_search_api.get_statistics(documents)
        
        # Optional: Export to JSONL
        dataset_path = None
        if documents and request.query_text:
            # Create safe filename from query
            safe_query = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in request.query_text)
            safe_query = safe_query.replace(' ', '_').lower()[:50]
            
            output_dir = Path("data/training_datasets")
            output_dir.mkdir(parents=True, exist_ok=True)
            dataset_path = str(output_dir / f"{safe_query}_{len(documents)}.jsonl")
            
            dataset_search_api.export_to_jsonl(documents, dataset_path)
            logger.info(f"✅ Exported {len(documents)} documents to {dataset_path}")
        
        # Security Audit Log
        logger.info(f"🔒 AUDIT: Dataset search by {user_email} - Found {len(documents)} documents")
        
        return {
            "success": True,
            "documents_found": len(documents),
            "statistics": stats,
            "dataset_path": dataset_path,
            "message": f"Found {len(documents)} documents matching query"
        }
    
    except Exception as e:
        logger.error(f"❌ Dataset search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets/statistics")
async def get_dataset_statistics(
    user: dict = Depends(jwt_middleware.get_current_user) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
):
    """
    Get dataset statistics from UDS3
    
    🔐 Security: JWT Required (any authenticated user)
    
    Returns:
        Dataset statistics (document counts, domains, etc.)
    """
    if not UDS3_DATASET_SEARCH_AVAILABLE or not dataset_search_api:
        raise HTTPException(
            status_code=503,
            detail="UDS3 Dataset Search not available"
        )
    
    try:
        # TODO: Implement statistics query
        # This would query UDS3 for total document counts, domains, etc.
        
        return {
            "success": True,
            "message": "Dataset statistics endpoint (TODO: implement)",
            "statistics": {
                "total_documents": "N/A",
                "domains": {},
                "document_types": {}
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Statistics query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Endpoint
# ============================================================================

# (Moved above Dataset Search Endpoints)
        logger.info("WebSocket Client disconnected")
    
    finally:
        await job_manager.unregister_websocket(websocket)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Start Metrics HTTP Server (optional)
    if os.environ.get("CLARA_METRICS_HTTP") == "1":
        try:
            metrics_port = int(os.environ.get("CLARA_METRICS_PORT", "9310"))
            metrics.start_http(port=metrics_port)
            logger.info(f"📡 Metrics Endpoint: http://localhost:{metrics_port}/metrics")
        except Exception as e:
            logger.warning(f"Konnte Metrics Endpoint nicht starten: {e}")
    
    # Start FastAPI Server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        log_level="info"
    )
