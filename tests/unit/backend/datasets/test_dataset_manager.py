"""
Unit Tests for Dataset Manager

Tests the DatasetManager class in isolation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.datasets.manager import DatasetManager
from backend.datasets.models import Dataset, DatasetStatus, ExportFormat


class TestDatasetManager:
    """Test DatasetManager class"""
    
    @pytest.fixture
    def manager(self):
        """Create a DatasetManager instance"""
        return DatasetManager()
    
    def test_manager_initialization(self, manager):
        """Test manager initializes correctly"""
        assert len(manager.datasets) == 0
    
    def test_create_dataset(self, manager):
        """Test dataset creation"""
        dataset = manager.create_dataset(
            name="test-dataset",
            description="Test description",
            user_email="test@example.com"
        )
        
        assert dataset.id is not None
        assert dataset.name == "test-dataset"
        assert dataset.status == DatasetStatus.PENDING
        assert dataset.user_email == "test@example.com"
        assert dataset.id in manager.datasets
    
    def test_get_dataset(self, manager):
        """Test retrieving a dataset by ID"""
        dataset = manager.create_dataset(
            name="test-dataset",
            description="Test description",
            user_email="test@example.com"
        )
        
        retrieved = manager.get_dataset(dataset.id)
        
        assert retrieved is not None
        assert retrieved.id == dataset.id
        assert retrieved.name == dataset.name
    
    def test_get_nonexistent_dataset(self, manager):
        """Test retrieving a non-existent dataset returns None"""
        dataset = manager.get_dataset("nonexistent-id")
        assert dataset is None
    
    def test_list_datasets(self, manager):
        """Test listing all datasets"""
        dataset1 = manager.create_dataset(
            name="dataset-1",
            description="First dataset",
            user_email="user1@example.com"
        )
        dataset2 = manager.create_dataset(
            name="dataset-2",
            description="Second dataset",
            user_email="user2@example.com"
        )
        
        datasets = manager.list_datasets()
        
        assert len(datasets) == 2
        assert dataset1 in datasets
        assert dataset2 in datasets
    
    def test_delete_dataset(self, manager):
        """Test deleting a dataset"""
        dataset = manager.create_dataset(
            name="test-dataset",
            description="Test description",
            user_email="test@example.com"
        )
        
        success = manager.delete_dataset(dataset.id)
        
        assert success is True
        assert manager.get_dataset(dataset.id) is None
    
    def test_delete_nonexistent_dataset(self, manager):
        """Test deleting a non-existent dataset fails gracefully"""
        success = manager.delete_dataset("nonexistent-id")
        assert success is False


class TestDataset:
    """Test Dataset model"""
    
    def test_dataset_creation(self):
        """Test dataset model creation"""
        dataset = Dataset(
            id="test-id",
            name="test-dataset",
            description="Test description",
            status=DatasetStatus.PENDING,
            user_email="test@example.com",
            created_at=datetime.now()
        )
        
        assert dataset.id == "test-id"
        assert dataset.name == "test-dataset"
        assert dataset.status == DatasetStatus.PENDING
        assert dataset.user_email == "test@example.com"
    
    def test_dataset_status_transitions(self):
        """Test dataset status can be updated"""
        dataset = Dataset(
            id="test-id",
            name="test-dataset",
            description="Test description",
            status=DatasetStatus.PENDING,
            user_email="test@example.com",
            created_at=datetime.now()
        )
        
        # Transition to processing
        dataset.status = DatasetStatus.PROCESSING
        assert dataset.status == DatasetStatus.PROCESSING
        
        # Transition to ready
        dataset.status = DatasetStatus.READY
        assert dataset.status == DatasetStatus.READY


class TestExportFormat:
    """Test ExportFormat enum"""
    
    def test_export_formats(self):
        """Test all export formats are available"""
        assert ExportFormat.JSONL == "jsonl"
        assert ExportFormat.PARQUET == "parquet"
        assert ExportFormat.CSV == "csv"
        assert ExportFormat.JSON == "json"
    
    def test_format_validation(self):
        """Test format validation"""
        # Valid formats
        assert ExportFormat("jsonl") == ExportFormat.JSONL
        assert ExportFormat("parquet") == ExportFormat.PARQUET
        
        # Invalid format
        with pytest.raises(ValueError):
            ExportFormat("invalid")
