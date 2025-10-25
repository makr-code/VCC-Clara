# Fügt src/ dem sys.path hinzu für Tests ohne Installation als Paket
import sys
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ===== Environment Setup for Tests =====
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Set up test environment variables.
    Runs once per test session automatically.
    """
    os.environ["CLARA_ENVIRONMENT"] = "testing"
    os.environ["CLARA_SECURITY_MODE"] = "testing"
    os.environ["CLARA_DEBUG"] = "true"
    os.environ["CLARA_LOG_LEVEL"] = "DEBUG"
    os.environ["CLARA_JWT_ENABLED"] = "false"
    os.environ["CLARA_MTLS_ENABLED"] = "false"
    os.environ["UDS3_ENABLED"] = "false"
    
    yield
    
    # Cleanup (if needed)
    pass


# ===== Config Fixtures =====
@pytest.fixture
def test_config():
    """Provide testing configuration"""
    from config import get_config
    return get_config("testing")


@pytest.fixture
def dev_config():
    """Provide development configuration"""
    from config import get_config
    return get_config("development")


@pytest.fixture
def prod_config():
    """Provide production configuration"""
    from config import get_config
    return get_config("production")


# ===== Backend Fixtures =====
@pytest.fixture
def training_manager():
    """Provide a TrainingJobManager instance for testing"""
    from backend.training.manager import TrainingJobManager
    return TrainingJobManager(max_concurrent_jobs=1)


@pytest.fixture
def dataset_manager():
    """Provide a DatasetManager instance for testing"""
    from backend.datasets.manager import DatasetManager
    return DatasetManager()


# ===== Model Fixtures =====
@pytest.fixture
def sample_training_config():
    """Provide a sample TrainingConfig for tests"""
    from backend.training.models import TrainingConfig
    return TrainingConfig(
        model_name="test-model",
        dataset_path="test-data.jsonl",
        output_dir="test-output",
        epochs=3,
        learning_rate=0.0001
    )


@pytest.fixture
def sample_dataset_request():
    """Provide a sample dataset request for tests"""
    return {
        "name": "test-dataset",
        "description": "Test dataset for integration tests",
        "filters": {
            "min_length": 10,
            "max_length": 1000
        }
    }


# ===== Path Fixtures =====
@pytest.fixture
def test_data_dir(tmp_path):
    """Provide a temporary directory for test data"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def test_output_dir(tmp_path):
    """Provide a temporary directory for test outputs"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# ===== Mock Fixtures =====
@pytest.fixture
def mock_uds3_strategy():
    """Provide a mock UDS3 strategy for testing"""
    from unittest.mock import Mock
    
    mock = Mock()
    mock.search.return_value = []
    mock.count.return_value = 0
    
    return mock


# ===== Integration Test Fixtures =====
@pytest.fixture
def backend_url():
    """Provide backend URL for integration tests"""
    return "http://localhost:45681"  # Dataset backend port


@pytest.fixture
def training_backend_url():
    """Provide training backend URL for integration tests"""
    return "http://localhost:45680"  # Training backend port


# ===== Pytest Configuration =====
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (require services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (full workflow)"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests (may take several seconds)"
    )

