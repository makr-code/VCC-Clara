"""
Dataset Manager with UDS3 Integration

Features:
- Dataset search and creation
- Quality pipeline
- Multi-format export
- Dataset versioning
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .models import Dataset, DatasetStatus, DatasetSearchRequest, ExportFormat
from .export import DatasetExporter

logger = logging.getLogger(__name__)

# UDS3 Dataset Search Import (optional)
try:
    from shared.database import (
        DatasetSearchAPI, 
        DatasetSearchQuery, 
        DatasetDocument,
        UDS3_AVAILABLE
    )
    UDS3_DATASET_SEARCH_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ UDS3 Dataset Search not available")
    UDS3_DATASET_SEARCH_AVAILABLE = False
    DatasetSearchAPI = None
    UDS3_AVAILABLE = False


class DatasetManager:
    """
    Dataset Manager with UDS3 Integration
    
    Features:
    - Dataset search and creation via UDS3
    - Quality pipeline integration
    - Multi-format export (JSONL, Parquet, CSV, JSON)
    - Dataset versioning and metadata tracking
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
                export_path = DatasetExporter.export(
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
    
    def get_dataset(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID"""
        return self.datasets.get(dataset_id)
    
    def list_datasets(self) -> List[Dataset]:
        """List all datasets"""
        return list(self.datasets.values())
