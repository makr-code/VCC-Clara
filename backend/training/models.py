"""
Training Backend Models

Pydantic Models und Dataclasses für Training Backend Service
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from pydantic import BaseModel, Field, validator
from pathlib import Path


# ============================================================================
# Enums
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


# ============================================================================
# Dataclass Models
# ============================================================================

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
