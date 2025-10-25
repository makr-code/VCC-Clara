"""
API Client for Dataset Backend

Handles communication with Dataset Backend microservice (Port 45681).
"""

import requests
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class DatasetAPIClient:
    """
    Dataset Backend API Client
    
    Communicates with clara_dataset_backend service on port 45681.
    Handles dataset creation, export, and management.
    """
    
    def __init__(self, base_url: str = "http://localhost:45681"):
        """
        Initialize Dataset API Client
        
        Args:
            base_url: Base URL of dataset backend
        """
        self.base_url = base_url
        self.api_prefix = f"{base_url}/api/datasets"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Clara-Frontend/2.0'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check service health
        
        Returns:
            Health status dict
            
        Raises:
            requests.RequestException: On connection error
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    def create_dataset(
        self,
        name: str,
        description: str,
        query_text: str,
        top_k: int = 100,
        min_quality_score: float = 0.5,
        search_types: Optional[List[str]] = None,
        export_formats: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create new dataset from search query
        
        Args:
            name: Dataset name (alphanumeric + spaces + underscores)
            description: Dataset description
            query_text: Search query text
            top_k: Number of results to fetch
            min_quality_score: Minimum quality threshold (0.0-1.0)
            search_types: Search methods (vector, graph, relational)
            export_formats: Export formats (jsonl, parquet, csv)
            filters: Domain/type filters
            
        Returns:
            Dataset creation response with dataset_id
            
        Raises:
            requests.RequestException: On API error
        """
        payload = {
            "name": name,
            "description": description,
            "search_query": {
                "query_text": query_text,
                "top_k": top_k,
                "min_quality_score": min_quality_score,
                "search_types": search_types or ["vector", "graph"],
                "filters": filters or {}
            },
            "export_formats": export_formats or ["jsonl"]
        }
        
        try:
            response = self.session.post(
                self.api_prefix,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Dataset creation failed: {e}")
            raise
    
    def get_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get dataset details by ID
        
        Args:
            dataset_id: Dataset UUID
            
        Returns:
            Dataset details dict
            
        Raises:
            requests.RequestException: On API error
        """
        try:
            response = self.session.get(
                f"{self.api_prefix}/{dataset_id}",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Get dataset failed: {e}")
            raise
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """
        List all datasets
        
        Returns:
            List of dataset dicts
            
        Raises:
            requests.RequestException: On API error
        """
        try:
            response = self.session.get(
                self.api_prefix,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return list(data.get("datasets", {}).values())
        except requests.RequestException as e:
            logger.error(f"List datasets failed: {e}")
            raise
    
    def delete_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Delete dataset
        
        Args:
            dataset_id: Dataset UUID
            
        Returns:
            Deletion response
            
        Raises:
            requests.RequestException: On API error
        """
        try:
            response = self.session.delete(
                f"{self.api_prefix}/{dataset_id}",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Delete dataset failed: {e}")
            raise
    
    def export_dataset(
        self,
        dataset_id: str,
        export_format: str = "jsonl"
    ) -> Dict[str, Any]:
        """
        Export dataset to file
        
        Args:
            dataset_id: Dataset UUID
            export_format: Format (jsonl, parquet, csv, json)
            
        Returns:
            Export response with file path
            
        Raises:
            requests.RequestException: On API error
        """
        payload = {
            "format": export_format
        }
        
        try:
            response = self.session.post(
                f"{self.api_prefix}/{dataset_id}/export",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Export dataset failed: {e}")
            raise
    
    def is_connected(self) -> bool:
        """
        Check if backend is reachable
        
        Returns:
            True if connected, False otherwise
        """
        try:
            self.health_check()
            return True
        except:
            return False
