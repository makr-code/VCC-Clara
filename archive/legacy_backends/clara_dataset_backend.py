#!/usr/bin/env python3
"""
CLARA Dataset Management Backend Service
FastAPI Microservice für Dataset-Vorbereitung und -Verwaltung

Port: 45681
Verantwortlichkeiten:
- UDS3 Hybrid Search Integration
- Dataset Quality Pipeline
- Dataset Export (JSONL, Parquet, CSV)
- Dataset Registry (PostgreSQL)
- Batch Processing
- Dataset Versioning

Architecture:
    Training Backend (45680) → Dataset Backend (45681) → UDS3 (PostgreSQL, ChromaDB, Neo4j)

Author: VCC Team
Date: 2024-10-24
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
from dataclasses import dataclass, asdict, field

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
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
    logging.warning("JWT Middleware not available - running in DEBUG mode")
    JWT_AVAILABLE = False
    jwt_middleware = None

# UDS3 Dataset Search Import (new location)
try:
    from shared.database import (
        DatasetSearchAPI, 
        DatasetSearchQuery, 
        DatasetDocument,
        UDS3_AVAILABLE
    )
    UDS3_DATASET_SEARCH_AVAILABLE = True
except ImportError:
    logging.warning("UDS3 Dataset Search not available")
    UDS3_DATASET_SEARCH_AVAILABLE = False
    DatasetSearchAPI = None
    UDS3_AVAILABLE = False

# Setup Logging
from src.utils.logger import setup_logger
logger = setup_logger(__name__)


# ============================================================================
# Configuration
# ============================================================================

SERVICE_NAME = "clara_dataset_backend"
# Use config if available, otherwise fallback to env vars
if CONFIG_AVAILABLE and config:
    SERVICE_PORT = config.dataset_port
else:
    SERVICE_PORT = int(os.environ.get("CLARA_DATASET_PORT", "45681"))


# ============================================================================
# Data Models
# ============================================================================

class DatasetStatus(str, Enum):
    """Dataset Status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    """Export Formats"""
    JSONL = "jsonl"
    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"


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
    """Request model for dataset search"""
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


# ============================================================================
# Dataset Manager
# ============================================================================

class DatasetManager:
    """
    Dataset Manager with UDS3 Integration
    
    Features:
    - Dataset search and creation
    - Quality pipeline
    - Multi-format export
    - Dataset versioning
    """
    
    def __init__(self):
        self.datasets: Dict[str, Dataset] = {}
        self.search_api: Optional[Any] = None
        
        # Initialize UDS3 Search API
        if UDS3_DATASET_SEARCH_AVAILABLE and DatasetSearchAPI:
            try:
                self.search_api = DatasetSearchAPI()
                logger.info("✅ DatasetManager initialized with UDS3 Search API")
            except Exception as e:
                logger.warning(f"⚠️ UDS3 Search API initialization failed: {e}")
        else:
            logger.warning("⚠️ UDS3 Search API not available")
    
    async def create_dataset(
        self,
        name: str,
        description: str,
        search_query: DatasetSearchRequest,
        export_formats: List[ExportFormat],
        created_by: str
    ) -> Dataset:
        """
        Create new dataset from search query
        
        Args:
            name: Dataset name
            description: Dataset description
            search_query: Search configuration
            export_formats: Export formats to generate
            created_by: User who created dataset
            
        Returns:
            Dataset object
        """
        dataset_id = str(uuid.uuid4())
        
        dataset = Dataset(
            dataset_id=dataset_id,
            name=name,
            description=description,
            status=DatasetStatus.PENDING,
            created_at=datetime.now(),
            created_by=created_by,
            query_text=search_query.query_text
        )
        
        self.datasets[dataset_id] = dataset
        logger.info(f"📦 Dataset created: {dataset_id} ({name})")
        
        return dataset
    
    async def process_dataset(
        self,
        dataset: Dataset,
        search_query: DatasetSearchRequest,
        export_formats: List[ExportFormat]
    ):
        """
        Process dataset: search, filter, export
        
        Args:
            dataset: Dataset object
            search_query: Search configuration
            export_formats: Export formats
        """
        try:
            dataset.status = DatasetStatus.PROCESSING
            logger.info(f"🔄 Processing dataset: {dataset.dataset_id}")
            
            # Step 1: Search documents via UDS3
            if not self.search_api:
                raise ValueError("UDS3 Search API not available")
            
            query = DatasetSearchQuery(
                query_text=search_query.query_text,
                top_k=search_query.top_k,
                filters=search_query.filters,
                min_quality_score=search_query.min_quality_score,
                search_types=search_query.search_types,
                weights=search_query.weights
            )
            
            documents = await self.search_api.search_datasets(query)
            
            # Step 2: Calculate statistics
            stats = self.search_api.get_statistics(documents)
            dataset.document_count = stats["total_documents"]
            dataset.total_tokens = stats["total_tokens"]
            dataset.quality_score_avg = stats["avg_quality_score"]
            dataset.metadata["statistics"] = stats
            
            # Step 3: Export to requested formats
            base_dir = Path("data/datasets") / dataset.dataset_id
            base_dir.mkdir(parents=True, exist_ok=True)
            
            for format in export_formats:
                export_path = await self._export_dataset(
                    documents=documents,
                    dataset=dataset,
                    format=format,
                    base_dir=base_dir
                )
                dataset.export_paths[format.value] = str(export_path)
            
            dataset.status = DatasetStatus.COMPLETED
            logger.info(f"✅ Dataset processed: {dataset.dataset_id} ({dataset.document_count} docs)")
        
        except Exception as e:
            dataset.status = DatasetStatus.FAILED
            dataset.metadata["error"] = str(e)
            logger.error(f"❌ Dataset processing failed: {dataset.dataset_id} - {e}")
            raise
    
    async def _export_dataset(
        self,
        documents: List[Any],  # DatasetDocument
        dataset: Dataset,
        format: ExportFormat,
        base_dir: Path
    ) -> Path:
        """
        Export dataset to specified format
        
        Args:
            documents: List of DatasetDocument objects
            dataset: Dataset metadata
            format: Export format
            base_dir: Base directory for exports
            
        Returns:
            Path to exported file
        """
        logger.info(f"📤 Exporting dataset to {format.value}: {dataset.dataset_id}")
        
        # Safe filename
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in dataset.name)
        
        if format == ExportFormat.JSONL:
            # JSONL format (one JSON object per line)
            output_file = base_dir / f"{safe_name}.jsonl"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for doc in documents:
                    training_entry = doc.to_training_format()
                    f.write(json.dumps(training_entry, ensure_ascii=False) + '\n')
            
            logger.info(f"✅ Exported {len(documents)} documents to JSONL")
        
        elif format == ExportFormat.PARQUET:
            # Parquet format (columnar storage)
            output_file = base_dir / f"{safe_name}.parquet"
            
            try:
                import pandas as pd
                import pyarrow as pa
                import pyarrow.parquet as pq
                
                # Convert to DataFrame
                data = [doc.to_training_format() for doc in documents]
                df = pd.DataFrame(data)
                
                # Write Parquet
                table = pa.Table.from_pandas(df)
                pq.write_table(table, output_file)
                
                logger.info(f"✅ Exported {len(documents)} documents to Parquet")
            
            except ImportError:
                logger.warning("⚠️ pandas/pyarrow not installed - falling back to JSONL")
                output_file = base_dir / f"{safe_name}.jsonl"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for doc in documents:
                        f.write(json.dumps(doc.to_training_format(), ensure_ascii=False) + '\n')
        
        elif format == ExportFormat.CSV:
            # CSV format
            output_file = base_dir / f"{safe_name}.csv"
            
            try:
                import csv
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    if documents:
                        fieldnames = ['document_id', 'text', 'source', 'quality_score', 'relevance_score']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for doc in documents:
                            entry = doc.to_training_format()
                            writer.writerow({
                                'document_id': entry['document_id'],
                                'text': entry['text'],
                                'source': entry['source'],
                                'quality_score': entry['quality_score'],
                                'relevance_score': entry['relevance_score']
                            })
                
                logger.info(f"✅ Exported {len(documents)} documents to CSV")
            
            except Exception as e:
                logger.error(f"CSV export failed: {e}")
                raise
        
        elif format == ExportFormat.JSON:
            # JSON format (single array)
            output_file = base_dir / f"{safe_name}.json"
            
            data = {
                "dataset_id": dataset.dataset_id,
                "name": dataset.name,
                "description": dataset.description,
                "created_at": dataset.created_at.isoformat(),
                "created_by": dataset.created_by,
                "document_count": len(documents),
                "documents": [doc.to_training_format() for doc in documents]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Exported {len(documents)} documents to JSON")
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return output_file
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID"""
        return self.datasets.get(dataset_id)
    
    def list_datasets(self) -> List[Dataset]:
        """List all datasets"""
        return list(self.datasets.values())


# ============================================================================
# FastAPI Application
# ============================================================================

# Global Dataset Manager
dataset_manager: Optional[DatasetManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan für Startup/Shutdown"""
    global dataset_manager
    
    # Startup
    logger.info("🚀 Dataset Backend startet...")
    
    dataset_manager = DatasetManager()
    
    logger.info(f"✅ Dataset Backend bereit (Port {SERVICE_PORT})")
    
    # Yield control
    yield
    
    # Shutdown
    logger.info("🛑 Dataset Backend wird gestoppt...")
    logger.info("✅ Shutdown abgeschlossen")


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


# ============================================================================
# API Endpoints
# ============================================================================

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


@app.post("/api/datasets", response_model=DatasetResponse)
async def create_dataset(
    request: DatasetCreateRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer", "analyst"])) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
):
    """
    Create new dataset from search query
    
    🔐 Security: JWT Required, Roles: admin OR trainer OR analyst
    
    Args:
        request: Dataset creation request
        background_tasks: FastAPI background tasks
        user: Authenticated user
        
    Returns:
        Dataset response with dataset_id and status
    """
    if not dataset_manager:
        raise HTTPException(status_code=503, detail="Dataset Manager not initialized")
    
    try:
        user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
        logger.info(f"📝 Creating dataset: {request.name} - User: {user_email}")
        
        # Create dataset
        dataset = await dataset_manager.create_dataset(
            name=request.name,
            description=request.description,
            search_query=request.search_query,
            export_formats=request.export_formats,
            created_by=user_email
        )
        
        # Process in background
        background_tasks.add_task(
            dataset_manager.process_dataset,
            dataset,
            request.search_query,
            request.export_formats
        )
        
        # Security Audit Log
        logger.info(f"🔒 AUDIT: Dataset {dataset.dataset_id} created by {user_email}")
        
        return DatasetResponse(
            success=True,
            dataset_id=dataset.dataset_id,
            status=dataset.status,
            message=f"Dataset created: {dataset.dataset_id}",
            data=dataset.to_dict()
        )
    
    except Exception as e:
        logger.error(f"❌ Dataset creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    user: dict = Depends(jwt_middleware.get_current_user) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
):
    """
    Get dataset details by ID
    
    🔐 Security: JWT Required (any authenticated user)
    
    Args:
        dataset_id: Dataset ID
        user: Authenticated user
        
    Returns:
        Dataset details
    """
    if not dataset_manager:
        raise HTTPException(status_code=503, detail="Dataset Manager not initialized")
    
    dataset = dataset_manager.get_dataset(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    return DatasetResponse(
        success=True,
        dataset_id=dataset.dataset_id,
        status=dataset.status,
        message="Dataset details retrieved",
        data=dataset.to_dict()
    )


@app.get("/api/datasets", response_model=DatasetListResponse)
async def list_datasets(
    user: dict = Depends(jwt_middleware.get_current_user) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
):
    """
    List all datasets
    
    🔐 Security: JWT Required (any authenticated user)
    
    Returns:
        List of all datasets
    """
    if not dataset_manager:
        raise HTTPException(status_code=503, detail="Dataset Manager not initialized")
    
    datasets = dataset_manager.list_datasets()
    
    return DatasetListResponse(
        datasets=[d.to_dict() for d in datasets],
        total_count=len(datasets)
    )


@app.post("/api/datasets/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    request: ExportRequest,
    user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer"])) if JWT_AVAILABLE else Depends(lambda: {"email": "dev@local"})
):
    """
    Export dataset to additional format
    
    🔐 Security: JWT Required, Roles: admin OR trainer
    
    Args:
        dataset_id: Dataset ID
        request: Export request (format)
        user: Authenticated user
        
    Returns:
        Export status
    """
    if not dataset_manager:
        raise HTTPException(status_code=503, detail="Dataset Manager not initialized")
    
    dataset = dataset_manager.get_dataset(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    if dataset.status != DatasetStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Dataset not ready (status: {dataset.status.value})")
    
    user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
    logger.info(f"📤 Exporting dataset {dataset_id} to {request.format.value} - User: {user_email}")
    
    # TODO: Implement re-export logic
    # For now, return existing export path if available
    
    export_path = dataset.export_paths.get(request.format.value)
    
    if export_path:
        return {
            "success": True,
            "message": f"Dataset already exported to {request.format.value}",
            "export_path": export_path
        }
    else:
        return {
            "success": False,
            "message": f"Dataset not yet exported to {request.format.value}. Re-export not implemented."
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
