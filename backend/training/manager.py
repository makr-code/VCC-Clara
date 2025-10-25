"""
Training Job Manager with Worker Pool

Analog zu Ingestion Backend Job Management (docs/MICROSERVICES_ARCHITECTURE.md)
"""

import asyncio
import logging
import uuid
import time
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from fastapi import WebSocket

from .models import TrainingJob, JobStatus, TrainerType, JobUpdateMessage

logger = logging.getLogger(__name__)


class TrainingJobManager:
    """
    Zentrale Job-Verwaltung mit Worker Pool
    
    Features:
    - Async Worker Pool für parallele Job-Verarbeitung
    - WebSocket Broadcasting für Live-Updates
    - Job Queue Management
    - Metrics Tracking
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
    
    def create_job(self, request) -> TrainingJob:
        """
        Erstellt neuen Training Job
        
        Args:
            request: TrainingJobRequest with config
            
        Returns:
            Created TrainingJob instance
        """
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
            
            logger.info(f"✅ Job completed: {job.job_id}")
            
        except Exception as e:
            # Failure
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            job.error_message = str(e)
            
            logger.error(f"❌ Job failed: {job.job_id} - {e}")
        
        finally:
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
        
        # TODO: Integrate with scripts/clara_train_lora.py
        logger.warning("⚠️ Using simulated training (TODO: integrate real trainer)")
        return self._simulate_training_sync(job, config)
    
    def _run_qlora_training_sync(self, job: TrainingJob, config: Dict) -> Dict[str, Any]:
        """Run QLoRA Training (Sync)"""
        logger.info(f"🔧 QLoRA Training: {job.job_id}")
        
        # TODO: Integrate with scripts/clara_train_qlora.py
        logger.warning("⚠️ Using simulated training (TODO: integrate real trainer)")
        return self._simulate_training_sync(job, config)
    
    def _run_continuous_training_sync(self, job: TrainingJob, config: Dict) -> Dict[str, Any]:
        """Run Continuous Learning Training (Sync)"""
        logger.info(f"🔧 Continuous Learning Training: {job.job_id}")
        
        # TODO: Integrate with scripts/clara_continuous_learning.py
        logger.warning("⚠️ Continuous Learning not yet implemented - simulating")
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
