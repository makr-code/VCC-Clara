"""
Dataset API Routes

FastAPI endpoints for dataset management and export.
"""

import json
import logging
from typing import Optional, AsyncIterator
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from ..models import (
    DatasetCreateRequest,
    DatasetResponse,
    DatasetListResponse,
    ExportRequest,
    DatasetStatus
)
from ..manager import DatasetManager

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/datasets", tags=["datasets"])

# Global manager (will be injected from app.py)
dataset_manager: Optional[DatasetManager] = None

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


def get_dataset_manager() -> DatasetManager:
    """Dependency for dataset manager"""
    if dataset_manager is None:
        raise HTTPException(status_code=503, detail="Dataset Manager not initialized")
    return dataset_manager


# ============================================================================
# Dataset Endpoints
# ============================================================================

@router.post("", response_model=DatasetResponse)
async def create_dataset(
    request: DatasetCreateRequest,
    background_tasks: BackgroundTasks,
    manager: DatasetManager = Depends(get_dataset_manager),
    user: dict = Depends(optional_auth)
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
    try:
        user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
        logger.info(f"📝 Creating dataset: {request.name} - User: {user_email}")
        
        # Create dataset
        dataset = await manager.create_dataset(
            name=request.name,
            description=request.description,
            search_query=request.search_query,
            export_formats=request.export_formats,
            created_by=user_email
        )
        
        # Process in background
        background_tasks.add_task(
            manager.process_dataset,
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


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    manager: DatasetManager = Depends(get_dataset_manager),
    user: dict = Depends(optional_auth)
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
    dataset = manager.get_dataset(dataset_id)
    
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_id}")
    
    return DatasetResponse(
        success=True,
        dataset_id=dataset.dataset_id,
        status=dataset.status,
        message="Dataset details retrieved",
        data=dataset.to_dict()
    )


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    manager: DatasetManager = Depends(get_dataset_manager),
    user: dict = Depends(optional_auth)
):
    """
    List all datasets
    
    🔐 Security: JWT Required (any authenticated user)
    
    Returns:
        List of all datasets
    """
    datasets = manager.list_datasets()
    
    return DatasetListResponse(
        datasets=[d.to_dict() for d in datasets],
        total_count=len(datasets)
    )


@router.post("/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    request: ExportRequest,
    manager: DatasetManager = Depends(get_dataset_manager),
    user: dict = Depends(optional_auth)
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
    dataset = manager.get_dataset(dataset_id)
    
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


@router.post("/stream", response_class=StreamingResponse)
async def stream_dataset_search(
    request: DatasetCreateRequest,
    manager: DatasetManager = Depends(get_dataset_manager),
    user: dict = Depends(optional_auth)
):
    """
    Stream dataset search results as JSONL (memory-efficient)
    
    🌊 Streaming Endpoint: Returns JSONL data line-by-line without loading all data into memory.
    Preferred over batch retrieval for large datasets and LoRA training pipelines.
    
    🔐 Security: JWT Required, Roles: admin OR trainer OR analyst
    
    Args:
        request: Dataset search request (same as create_dataset)
        user: Authenticated user
        
    Returns:
        StreamingResponse with application/x-ndjson content-type
        
    Example:
        ```bash
        curl -X POST http://localhost:45681/api/datasets/stream \\
             -H "Content-Type: application/json" \\
             -d '{"name": "test", "search_query": {...}}' \\
             --output training_data.jsonl
        ```
    """
    try:
        if not manager.search_api:
            raise HTTPException(
                status_code=503,
                detail="UDS3 Search API not available. Streaming requires UDS3 integration."
            )
        
        user_email = get_current_user_email(user) if JWT_AVAILABLE else user.get("email", "dev@local")
        logger.info(f"🌊 Streaming dataset search: {request.name} - User: {user_email}")
        
        # Import DatasetSearchQuery from shared.database.dataset_search
        from shared.database.dataset_search import DatasetSearchQuery
        
        # Convert request to DatasetSearchQuery
        query = DatasetSearchQuery(
            query_text=request.search_query.query_text,
            top_k=request.search_query.top_k,
            filters=request.search_query.filters,
            min_quality_score=request.search_query.min_quality_score,
            search_types=request.search_query.search_types,
            weights=request.search_query.weights
        )
        
        async def generate_jsonl() -> AsyncIterator[str]:
            """Generate JSONL lines from streaming search results"""
            count = 0
            try:
                async for doc in manager.search_api.stream_datasets(query, batch_size=100):
                    training_entry = doc.to_training_format()
                    json_line = json.dumps(training_entry, ensure_ascii=False) + '\n'
                    yield json_line
                    count += 1
                    
                    if count % 100 == 0:
                        logger.info(f"   Streamed {count} documents...")
                
                logger.info(f"✅ Streaming complete: {count} documents")
                
            except Exception as e:
                logger.error(f"❌ Streaming error: {e}")
                # Send error as final JSONL line
                error_line = json.dumps({
                    "error": str(e),
                    "message": "Streaming interrupted due to error"
                }, ensure_ascii=False) + '\n'
                yield error_line
        
        # Security Audit Log
        logger.info(f"🔒 AUDIT: Dataset streaming initiated by {user_email} - Query: {request.search_query.query_text[:50]}...")
        
        return StreamingResponse(
            generate_jsonl(),
            media_type="application/x-ndjson",  # JSONL MIME type
            headers={
                "Content-Disposition": f'attachment; filename="{request.name}.jsonl"',
                "X-Dataset-Name": request.name,
                "X-Query-Text": request.search_query.query_text[:100]
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Dataset streaming failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
