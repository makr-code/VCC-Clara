"""
Dataset Models

Data models for dataset management and export.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pydantic import BaseModel, Field, validator


# ============================================================================
# Enums
# ============================================================================

class DatasetStatus(str, Enum):
    """Dataset Processing Status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Supported Export Formats"""
    JSONL = "jsonl"
    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"


# ============================================================================
# Dataclasses
# ============================================================================

@dataclass
class Dataset:
    """
    Dataset Metadata
    
    Attributes:
        dataset_id: Unique dataset identifier
        name: Dataset name
        description: Dataset description
        status: Processing status
        created_at: Creation timestamp
        created_by: User who created dataset
        query_text: Search query used
        document_count: Number of documents
        total_tokens: Total token count
        quality_score_avg: Average quality score
        export_paths: Paths to exported files
        metadata: Additional metadata
    """
    dataset_id: str
    name: str
    description: str
    status: DatasetStatus
    created_at: datetime
    created_by: str
    query_text: Optional[str] = None
    document_count: int = 0
    total_tokens: int = 0
    quality_score_avg: float = 0.0
    export_paths: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data


# ============================================================================
# Pydantic Request/Response Models
# ============================================================================

class DatasetSearchRequest(BaseModel):
    """Request model for dataset search via UDS3"""
    query_text: str = Field(..., description="Search query")
    top_k: int = Field(100, ge=1, le=1000, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Domain/Type filters")
    min_quality_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum quality score")
    search_types: List[str] = Field(["vector", "graph"], description="Search methods")
    weights: Optional[Dict[str, float]] = Field(None, description="Search weights")


class DatasetCreateRequest(BaseModel):
    """Request model for dataset creation"""
    name: str = Field(..., description="Dataset name", min_length=3, max_length=100)
    description: str = Field("", description="Dataset description")
    search_query: DatasetSearchRequest = Field(..., description="Search configuration")
    export_formats: List[ExportFormat] = Field([ExportFormat.JSONL], description="Export formats")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate dataset name (alphanumeric, spaces, underscores)"""
        if not v.replace(" ", "").replace("_", "").isalnum():
            raise ValueError("Name must contain only alphanumeric characters, spaces, and underscores")
        return v


class DatasetResponse(BaseModel):
    """Response model for dataset operations"""
    success: bool
    dataset_id: str
    status: DatasetStatus
    message: str
    data: Optional[Dict[str, Any]] = None


class DatasetListResponse(BaseModel):
    """Response model for dataset list"""
    datasets: List[Dict[str, Any]]
    total_count: int


class ExportRequest(BaseModel):
    """Request model for dataset export"""
    format: ExportFormat = Field(..., description="Export format")
    include_metadata: bool = Field(True, description="Include metadata fields")
