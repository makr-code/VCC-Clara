"""
API Client for Training Backend

Handles communication with Training Backend microservice (Port 45680).
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TrainingAPIClient:
    """
    Training Backend API Client
    
    Communicates with clara_training_backend service on port 45680.
    Handles job creation, monitoring, and management.
    """
    
    def __init__(self, base_url: str = "http://localhost:45680"):
        """
        Initialize Training API Client
        
        Args:
            base_url: Base URL of training backend
        """
        self.base_url = base_url
        self.api_prefix = f"{base_url}/api/training"
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
    
    def create_job(
        self,
        trainer_type: str,
        config_path: str,
        dataset_path: str = "",
        priority: int = 1,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create new training job
        
        Args:
            trainer_type: Trainer type (lora, qlora, full_finetuning)
            config_path: Path to training config YAML
            dataset_path: Path to dataset (optional)
            priority: Job priority (1-10)
            tags: Optional tags for job
            
        Returns:
            Job creation response with job_id
            
        Raises:
            requests.RequestException: On API error
        """
        payload = {
            "trainer_type": trainer_type,
            "config_path": config_path,
            "dataset_path": dataset_path,
            "priority": priority,
            "tags": tags or []
        }
        
        try:
            response = self.session.post(
                f"{self.api_prefix}/jobs",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Job creation failed: {e}")
            raise
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get job details by ID
        
        Args:
            job_id: Job UUID
            
        Returns:
            Job details dict
            
        Raises:
            requests.RequestException: On API error
        """
        try:
            response = self.session.get(
                f"{self.api_prefix}/jobs/{job_id}",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Get job failed: {e}")
            raise
    
    def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all jobs (with optional filtering)
        
        Args:
            status: Filter by status (pending, running, completed, failed)
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dicts
            
        Raises:
            requests.RequestException: On API error
        """
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        try:
            response = self.session.get(
                f"{self.api_prefix}/jobs",
                params=params,
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return data.get("jobs", [])
        except requests.RequestException as e:
            logger.error(f"List jobs failed: {e}")
            raise
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel running job
        
        Args:
            job_id: Job UUID
            
        Returns:
            Cancellation response
            
        Raises:
            requests.RequestException: On API error
        """
        try:
            response = self.session.post(
                f"{self.api_prefix}/jobs/{job_id}/cancel",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Cancel job failed: {e}")
            raise
    
    def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """
        Get job training metrics
        
        Args:
            job_id: Job UUID
            
        Returns:
            Metrics dict with loss, accuracy, etc.
            
        Raises:
            requests.RequestException: On API error
        """
        try:
            response = self.session.get(
                f"{self.api_prefix}/jobs/{job_id}/metrics",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Get metrics failed: {e}")
            raise
    
    def get_worker_status(self) -> Dict[str, Any]:
        """
        Get worker pool status
        
        Returns:
            Worker status dict
            
        Raises:
            requests.RequestException: On API error
        """
        try:
            response = self.session.get(
                f"{self.api_prefix}/workers",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Get worker status failed: {e}")
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
