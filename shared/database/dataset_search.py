#!/usr/bin/env python3
"""
UDS3 Dataset Search Integration for CLARA Training System

Provides dataset discovery and selection via UDS3 Hybrid Search API.

Features:
- Search documents by query text
- Filter by domain, document_type, quality_score
- Export search results to training datasets (JSONL)
- Integration with Training Backend

Usage:
    from shared.uds3_dataset_search import DatasetSearchAPI, DatasetSearchQuery
    
    api = DatasetSearchAPI()
    results = await api.search_datasets(
        query="Verwaltungsrecht Photovoltaik",
        filters={"domain": "verwaltungsrecht"},
        top_k=100
    )
    
    # Export to JSONL for training
    api.export_to_jsonl(results, "datasets/training_data.jsonl")
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

# UDS3 Package Import (installed via: pip install -e ../uds3)
try:
    from uds3.search.search_api import UDS3SearchAPI, SearchQuery, SearchResult
    from uds3.core.polyglot_manager import UDS3PolyglotManager
    UDS3_AVAILABLE = True
    logger.info("✅ UDS3 package imported successfully")
except ImportError as e:
    UDS3_AVAILABLE = False
    UDS3SearchAPI = None
    SearchQuery = None
    SearchResult = None
    UDS3PolyglotManager = None
    logger.warning(f"⚠️ UDS3 not available: {e}")


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class DatasetSearchQuery:
    """
    Dataset Search Query for Training
    
    Attributes:
        query_text: Search query (e.g., "Verwaltungsrecht Photovoltaik")
        top_k: Number of results
        filters: Domain/Type filters (e.g., {"domain": "verwaltungsrecht"})
        min_quality_score: Minimum quality score (0.0-1.0)
        search_types: Search methods (["vector", "graph", "keyword"])
        weights: Score weights for hybrid search
    """
    query_text: str
    top_k: int = 100
    filters: Optional[Dict[str, Any]] = None
    min_quality_score: float = 0.5
    search_types: List[str] = field(default_factory=lambda: ["vector", "graph"])
    weights: Optional[Dict[str, float]] = None
    
    def to_uds3_query(self) -> Optional[Any]:
        """Convert to UDS3 SearchQuery"""
        if not UDS3_AVAILABLE or not SearchQuery:
            return None
        
        return SearchQuery(
            query_text=self.query_text,
            top_k=self.top_k,
            filters=self.filters,
            search_types=self.search_types,
            weights=self.weights
        )


@dataclass
class DatasetDocument:
    """
    Training Dataset Document
    
    Attributes:
        document_id: Unique ID
        content: Document text
        metadata: Domain, type, source, etc.
        score: Relevance score (0.0-1.0)
        quality_score: Content quality score (0.0-1.0)
    """
    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    quality_score: float = 0.5
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return asdict(self)
    
    def to_training_format(self) -> Dict:
        """
        Convert to training format (JSONL)
        
        Format:
            {
                "text": "...",
                "metadata": {...},
                "source": "uds3_search",
                "quality_score": 0.85
            }
        """
        return {
            "text": self.content,
            "metadata": self.metadata,
            "source": "uds3_search",
            "quality_score": self.quality_score,
            "document_id": self.document_id,
            "relevance_score": self.score
        }


# ============================================================================
# Dataset Search API
# ============================================================================

class DatasetSearchAPI:
    """
    UDS3 Dataset Search API for Training
    
    Wraps UDS3SearchAPI with training-specific functionality:
    - Quality filtering
    - Dataset export (JSONL)
    - Statistics & reporting
    """
    
    def __init__(self, uds3_strategy=None):
        """
        Initialize Dataset Search API
        
        Args:
            uds3_strategy: Optional UDS3PolyglotManager instance (auto-created if None)
        """
        self.uds3_strategy = uds3_strategy
        self.search_api = None
        
        if UDS3_AVAILABLE:
            try:
                if uds3_strategy is None and UDS3PolyglotManager:
                    # Auto-create UDS3PolyglotManager - reads config from uds3/config_local.py
                    backend_config = {
                        "relational": {"enabled": True},  # PostgreSQL (192.168.178.94:5432)
                        "vector": {"enabled": True},      # ChromaDB (192.168.178.94:8000)
                        "graph": {"enabled": True},       # Neo4j (192.168.178.94:7687)
                        "file": {"enabled": True}         # CouchDB (192.168.178.94:32770)
                    }
                    
                    logger.info("🔧 Initializing UDS3 PolyglotManager (auto-config from uds3/config_local.py)...")
                    self.uds3_strategy = UDS3PolyglotManager(
                        backend_config=backend_config,
                        enable_rag=False  # Disable RAG for dataset search
                    )
                    logger.info("✅ UDS3 PolyglotManager created")
                
                if self.uds3_strategy and hasattr(self.uds3_strategy, 'db_manager'):
                    # Create UDS3SearchAPI with db_manager
                    self.search_api = UDS3SearchAPI(self.uds3_strategy.db_manager)
                    logger.info("✅ DatasetSearchAPI initialized with UDS3 PolyglotManager")
                else:
                    logger.warning("⚠️ UDS3 PolyglotManager has no db_manager")
                    
            except Exception as e:
                logger.warning(f"⚠️ UDS3 initialization failed: {e}", exc_info=True)
                self.search_api = None
        else:
            logger.warning("⚠️ UDS3 not available - dataset search disabled")
    
    async def search_datasets(
        self,
        query: DatasetSearchQuery
    ) -> List[DatasetDocument]:
        """
        Search datasets using UDS3 Hybrid Search
        
        Args:
            query: Dataset search query
            
        Returns:
            List of DatasetDocument objects
        """
        if not self.search_api:
            logger.warning("UDS3 SearchAPI not available")
            return []
        
        try:
            # Convert to UDS3 query
            uds3_query = query.to_uds3_query()
            if not uds3_query:
                logger.error("Failed to convert query to UDS3 format")
                return []
            
            # Execute hybrid search
            logger.info(f"🔍 Searching datasets: '{query.query_text}' (top_k={query.top_k})")
            search_results = await self.search_api.hybrid_search(uds3_query)
            
            # Convert to DatasetDocument
            documents = []
            for result in search_results:
                # Quality filtering
                quality_score = self._calculate_quality_score(result)
                
                if quality_score < query.min_quality_score:
                    logger.debug(f"   Skipping low-quality doc: {result.document_id} (score={quality_score:.2f})")
                    continue
                
                doc = DatasetDocument(
                    document_id=result.document_id,
                    content=result.content,
                    metadata=result.metadata,
                    score=result.score,
                    quality_score=quality_score
                )
                documents.append(doc)
            
            logger.info(f"✅ Found {len(documents)} documents (after quality filter: {query.min_quality_score})")
            return documents
        
        except Exception as e:
            logger.error(f"❌ Dataset search failed: {e}")
            return []
    
    def _calculate_quality_score(self, result: Any) -> float:
        """
        Calculate quality score for search result
        
        Criteria:
        - Content length (prefer longer documents)
        - Metadata completeness
        - Relevance score
        
        Returns:
            Quality score 0.0-1.0
        """
        try:
            score = 0.0
            
            # Content length (max 0.4)
            content_len = len(result.content)
            if content_len > 1000:
                score += 0.4
            elif content_len > 500:
                score += 0.3
            elif content_len > 200:
                score += 0.2
            else:
                score += 0.1
            
            # Metadata completeness (max 0.3)
            metadata = result.metadata or {}
            required_fields = ["title", "domain", "document_type"]
            completeness = sum(1 for field in required_fields if field in metadata) / len(required_fields)
            score += completeness * 0.3
            
            # Relevance score (max 0.3)
            score += result.score * 0.3
            
            return min(score, 1.0)
        
        except Exception as e:
            logger.warning(f"Quality score calculation failed: {e}")
            return 0.5  # Default
    
    async def stream_datasets(
        self,
        query: DatasetSearchQuery,
        batch_size: int = 100
    ):
        """
        Stream datasets using UDS3 Hybrid Search (async generator)
        
        This method yields documents in batches for memory-efficient streaming.
        Preferred over search_datasets() for large datasets and training pipelines.
        
        Args:
            query: Dataset search query
            batch_size: Number of documents to fetch per batch
            
        Yields:
            DatasetDocument objects one at a time
            
        Example:
            ```python
            async for doc in api.stream_datasets(query):
                # Process document immediately
                train_on_document(doc)
            ```
        """
        if not self.search_api:
            logger.warning("UDS3 SearchAPI not available for streaming")
            return
        
        try:
            offset = 0
            total_yielded = 0
            
            logger.info(f"🌊 Streaming datasets: '{query.query_text}' (batch_size={batch_size})")
            
            while total_yielded < query.top_k:
                # Calculate batch size for this iteration
                remaining = query.top_k - total_yielded
                current_batch_size = min(batch_size, remaining)
                
                # Create batch query
                batch_query = DatasetSearchQuery(
                    query_text=query.query_text,
                    top_k=current_batch_size,
                    filters=query.filters,
                    min_quality_score=query.min_quality_score,
                    search_types=query.search_types,
                    weights=query.weights
                )
                
                # Convert to UDS3 query
                uds3_query = batch_query.to_uds3_query()
                if not uds3_query:
                    logger.error("Failed to convert query to UDS3 format")
                    break
                
                # Execute hybrid search for this batch
                search_results = await self.search_api.hybrid_search(uds3_query)
                
                if not search_results:
                    logger.info(f"✅ Streaming complete: {total_yielded} documents yielded")
                    break
                
                # Process and yield documents
                for result in search_results:
                    # Quality filtering
                    quality_score = self._calculate_quality_score(result)
                    
                    if quality_score < query.min_quality_score:
                        logger.debug(f"   Skipping low-quality doc: {result.document_id} (score={quality_score:.2f})")
                        continue
                    
                    doc = DatasetDocument(
                        document_id=result.document_id,
                        content=result.content,
                        metadata=result.metadata,
                        score=result.score,
                        quality_score=quality_score
                    )
                    
                    yield doc
                    total_yielded += 1
                    
                    if total_yielded >= query.top_k:
                        break
                
                offset += current_batch_size
                
                # Avoid infinite loop if we got fewer results than batch_size
                if len(search_results) < current_batch_size:
                    logger.info(f"✅ Streaming complete: {total_yielded} documents yielded (no more results)")
                    break
            
            logger.info(f"✅ Streaming finished: {total_yielded} documents total")
        
        except Exception as e:
            logger.error(f"❌ Dataset streaming failed: {e}")
            raise
    
    def export_to_jsonl(
        self,
        documents: List[DatasetDocument],
        output_path: str
    ) -> bool:
        """
        Export documents to JSONL training file
        
        Args:
            documents: List of DatasetDocument objects
            output_path: Output file path (e.g., "datasets/training_data.jsonl")
            
        Returns:
            True if successful
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for doc in documents:
                    training_entry = doc.to_training_format()
                    f.write(json.dumps(training_entry, ensure_ascii=False) + '\n')
            
            logger.info(f"✅ Exported {len(documents)} documents to {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            return False
    
    async def stream_to_jsonl(
        self,
        query: DatasetSearchQuery,
        output_path: str,
        batch_size: int = 100
    ) -> int:
        """
        Stream documents directly to JSONL file (memory-efficient)
        
        This method is preferred for large datasets as it doesn't load
        all documents into memory at once.
        
        Args:
            query: Dataset search query
            output_path: Output file path
            batch_size: Number of documents per streaming batch
            
        Returns:
            Number of documents exported
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            count = 0
            logger.info(f"🌊 Streaming to JSONL: {output_path}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                async for doc in self.stream_datasets(query, batch_size):
                    training_entry = doc.to_training_format()
                    f.write(json.dumps(training_entry, ensure_ascii=False) + '\n')
                    count += 1
                    
                    if count % 100 == 0:
                        logger.info(f"   Streamed {count} documents...")
            
            logger.info(f"✅ Streamed {count} documents to {output_path}")
            return count
        
        except Exception as e:
            logger.error(f"❌ Stream to JSONL failed: {e}")
            raise
    
    def get_statistics(self, documents: List[DatasetDocument]) -> Dict:
        """
        Get dataset statistics
        
        Args:
            documents: List of DatasetDocument objects
            
        Returns:
            Statistics dict
        """
        if not documents:
            return {
                "total_documents": 0,
                "avg_quality_score": 0.0,
                "avg_relevance_score": 0.0,
                "total_tokens": 0
            }
        
        stats = {
            "total_documents": len(documents),
            "avg_quality_score": sum(d.quality_score for d in documents) / len(documents),
            "avg_relevance_score": sum(d.score for d in documents) / len(documents),
            "total_tokens": sum(len(d.content.split()) for d in documents),
            "domains": {},
            "document_types": {}
        }
        
        # Domain/Type distribution
        for doc in documents:
            domain = doc.metadata.get("domain", "unknown")
            doc_type = doc.metadata.get("document_type", "unknown")
            
            stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
            stats["document_types"][doc_type] = stats["document_types"].get(doc_type, 0) + 1
        
        return stats


# ============================================================================
# FastAPI Integration Models
# ============================================================================

from pydantic import BaseModel, Field

class DatasetSearchRequest(BaseModel):
    """Request model for dataset search endpoint"""
    query_text: str = Field(..., description="Search query")
    top_k: int = Field(100, ge=1, le=1000, description="Number of results")
    filters: Optional[Dict[str, Any]] = Field(None, description="Domain/Type filters")
    min_quality_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum quality score")
    search_types: List[str] = Field(["vector", "graph"], description="Search methods")
    weights: Optional[Dict[str, float]] = Field(None, description="Search weights")


class DatasetSearchResponse(BaseModel):
    """Response model for dataset search endpoint"""
    success: bool
    documents_found: int
    statistics: Dict
    dataset_path: Optional[str] = None
    message: str


# ============================================================================
# Example Usage
# ============================================================================

async def example_usage():
    """Example: Search datasets and export to JSONL (batch mode)"""
    
    # Initialize API
    api = DatasetSearchAPI()
    
    # Create search query
    query = DatasetSearchQuery(
        query_text="Verwaltungsrecht Photovoltaik Dachanlage",
        top_k=100,
        filters={"domain": "verwaltungsrecht"},
        min_quality_score=0.6,
        search_types=["vector", "graph"],
        weights={"vector": 0.6, "graph": 0.4}
    )
    
    # Search datasets
    documents = await api.search_datasets(query)
    
    # Get statistics
    stats = api.get_statistics(documents)
    print(f"📊 Statistics:")
    print(f"   Total Documents: {stats['total_documents']}")
    print(f"   Avg Quality: {stats['avg_quality_score']:.2f}")
    print(f"   Avg Relevance: {stats['avg_relevance_score']:.2f}")
    print(f"   Total Tokens: {stats['total_tokens']}")
    
    # Export to JSONL
    if documents:
        output_path = "data/training_datasets/verwaltungsrecht_photovoltaik.jsonl"
        api.export_to_jsonl(documents, output_path)
        print(f"✅ Exported to {output_path}")


async def example_streaming():
    """Example: Stream datasets to JSONL (memory-efficient)"""
    
    # Initialize API
    api = DatasetSearchAPI()
    
    # Create search query
    query = DatasetSearchQuery(
        query_text="Verwaltungsrecht Photovoltaik Dachanlage",
        top_k=1000,  # Large dataset
        filters={"domain": "verwaltungsrecht"},
        min_quality_score=0.6,
        search_types=["vector", "graph"],
        weights={"vector": 0.6, "graph": 0.4}
    )
    
    # Stream to JSONL (preferred for large datasets)
    output_path = "data/training_datasets/verwaltungsrecht_photovoltaik_stream.jsonl"
    count = await api.stream_to_jsonl(query, output_path, batch_size=100)
    print(f"✅ Streamed {count} documents to {output_path}")
    
    # Alternative: Manual streaming for custom processing
    print("\n🌊 Manual streaming example:")
    doc_count = 0
    async for doc in api.stream_datasets(query, batch_size=100):
        # Process each document immediately (e.g., train LoRA adapter)
        print(f"   Document {doc_count+1}: {doc.document_id[:8]}... (quality: {doc.quality_score:.2f})")
        doc_count += 1
        if doc_count >= 10:  # Limit for demo
            break
    print(f"✅ Processed {doc_count} documents via streaming")


if __name__ == "__main__":
    # Test UDS3 availability
    print("=" * 60)
    print("UDS3 Dataset Search API - Test")
    print("=" * 60)
    print(f"UDS3 Available: {UDS3_AVAILABLE}")
    
    if UDS3_AVAILABLE:
        print("\n🔵 Running batch example...")
        asyncio.run(example_usage())
        
        print("\n🌊 Running streaming example...")
        asyncio.run(example_streaming())
    else:
        print("⚠️ UDS3 not available. Install dependencies:")
        print("   cd c:/VCC/uds3")
        print("   pip install -e .")
