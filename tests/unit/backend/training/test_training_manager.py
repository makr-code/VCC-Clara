"""
Unit Tests for Training Manager

Tests the TrainingJobManager class in isolation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.training.manager import TrainingJobManager
from backend.training.models import TrainingJob, JobStatus, TrainerType, TrainingJobRequest


class TestTrainingJobManager:
    """Test TrainingJobManager class"""
    
    @pytest.fixture
    def manager(self):
        """Create a TrainingJobManager instance"""
        return TrainingJobManager(max_concurrent_jobs=2)
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self, manager):
        """Test manager initializes correctly"""
        assert manager.max_concurrent_jobs == 2
        assert len(manager.jobs) == 0
        assert manager.worker_pool is None
    
    def test_create_job(self, manager):
        """Test job creation"""
        job_request = TrainingJobRequest(
            trainer_type=TrainerType.LORA,
            config_path="test-config.yaml",
            dataset_path="test-data.jsonl",
            priority=1
        )
        
        job = manager.create_job(job_request, user_email="test@example.com")
        
        assert job.job_id is not None
        assert job.status == JobStatus.PENDING
        assert job.trainer_type == TrainerType.LORA
        assert job.job_id in manager.jobs
    
    def test_get_job(self, manager):
        """Test retrieving a job by ID"""
        job_request = TrainingJobRequest(
            trainer_type=TrainerType.LORA,
            config_path="test-config.yaml"
        )
        
        job = manager.create_job(job_request, user_email="test@example.com")
        retrieved_job = manager.get_job(job.job_id)
        
        assert retrieved_job is not None
        assert retrieved_job.job_id == job.job_id
        assert retrieved_job.status == job.status
    
    def test_get_nonexistent_job(self, manager):
        """Test retrieving a non-existent job returns None"""
        job = manager.get_job("nonexistent-id")
        assert job is None
    
    def test_list_jobs(self, manager):
        """Test listing all jobs"""
        job_request = TrainingJobRequest(
            trainer_type=TrainerType.LORA,
            config_path="test-config.yaml"
        )
        
        job1 = manager.create_job(job_request, user_email="user1@example.com")
        job2 = manager.create_job(job_request, user_email="user2@example.com")
        
        jobs = manager.list_jobs()
        
        assert len(jobs) == 2
        assert job1 in jobs
        assert job2 in jobs


class TestTrainingJobRequest:
    """Test TrainingJobRequest model"""
    
    def test_request_required_fields(self):
        """Test that required fields are enforced"""
        with pytest.raises(ValueError):
            TrainingJobRequest()
    
    def test_request_valid_creation(self):
        """Test creating a valid request"""
        request = TrainingJobRequest(
            trainer_type=TrainerType.LORA,
            config_path="test-config.yaml",
            dataset_path="test-data.jsonl",
            priority=3
        )
        
        assert request.trainer_type == TrainerType.LORA
        assert request.config_path == "test-config.yaml"
        assert request.dataset_path == "test-data.jsonl"
        assert request.priority == 3


class TestTrainingJob:
    """Test TrainingJob model"""
    
    def test_job_creation(self):
        """Test job model creation"""
        job = TrainingJob(
            job_id="test-id",
            trainer_type=TrainerType.LORA,
            status=JobStatus.PENDING,
            config_path="test-config.yaml"
        )
        
        assert job.job_id == "test-id"
        assert job.status == JobStatus.PENDING
        assert job.trainer_type == TrainerType.LORA
        assert job.config_path == "test-config.yaml"
        assert job.created_at is not None
    
    def test_job_status_transitions(self):
        """Test job status can be updated"""
        job = TrainingJob(
            job_id="test-id",
            trainer_type=TrainerType.LORA,
            status=JobStatus.PENDING,
            config_path="test-config.yaml"
        )
        
        # Transition to queued
        job.status = JobStatus.QUEUED
        assert job.status == JobStatus.QUEUED
        
        # Transition to running
        job.status = JobStatus.RUNNING
        assert job.status == JobStatus.RUNNING
        
        # Transition to completed
        job.status = JobStatus.COMPLETED
        assert job.status == JobStatus.COMPLETED
    
    def test_job_to_dict(self):
        """Test job serialization to dict"""
        job = TrainingJob(
            job_id="test-id",
            trainer_type=TrainerType.LORA,
            status=JobStatus.PENDING,
            config_path="test-config.yaml"
        )
        
        job_dict = job.to_dict()
        
        assert job_dict["job_id"] == "test-id"
        assert job_dict["status"] == "pending"
        assert job_dict["trainer_type"] == "lora"
        assert "created_at" in job_dict

