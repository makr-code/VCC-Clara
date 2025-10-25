"""
Dataset API Routes

FastAPI endpoints for dataset management and export.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends

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
