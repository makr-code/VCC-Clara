# Clara Test Suite

Organized test structure following best practices with unit, integration, and end-to-end tests.

## 📁 Test Structure

```
tests/
├── conftest.py                 # Global pytest configuration and fixtures
├── pytest.ini                  # Pytest settings
│
├── unit/                       # Unit Tests (fast, isolated)
│   ├── backend/
│   │   ├── training/
│   │   │   └── test_training_manager.py
│   │   └── datasets/
│   │       └── test_dataset_manager.py
│   ├── shared/                 # Shared module tests
│   └── config/                 # Config package tests
│       └── test_config.py
│
├── integration/                # Integration Tests (require services)
│   └── backend/
│       ├── test_dataset_backend_integration.py
│       └── test_security_integration.py
│
└── e2e/                        # End-to-End Tests (full workflow)
    └── (future tests)
```

## 🏃 Running Tests

### All Tests
```bash
pytest
```

### Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Integration Tests Only
```bash
pytest tests/integration/ -v
```

### Specific Test File
```bash
pytest tests/unit/config/test_config.py -v
```

### Specific Test Class
```bash
pytest tests/unit/config/test_config.py::TestBaseConfig -v
```

### Specific Test Method
```bash
pytest tests/unit/config/test_config.py::TestBaseConfig::test_default_config_loads -v
```

### By Marker
```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# Exclude slow tests
pytest -m "not slow" -v
```

### By Keyword
```bash
pytest -k "config" -v          # All tests with "config" in name
pytest -k "test_create" -v     # All tests starting with "test_create"
pytest -k "manager" -v         # All tests with "manager" in name
```

## 📊 Test Markers

Tests can be marked with the following markers:

- **@pytest.mark.unit** - Unit tests (fast, isolated)
- **@pytest.mark.integration** - Integration tests (require services)
- **@pytest.mark.e2e** - End-to-end tests (full workflow)
- **@pytest.mark.slow** - Slow tests (may take several seconds)

Example:
```python
@pytest.mark.unit
def test_config_loads():
    ...

@pytest.mark.integration
@pytest.mark.slow
def test_full_dataset_workflow():
    ...
```

## 🔧 Fixtures

Available fixtures from `conftest.py`:

### Config Fixtures
- `test_config` - Testing configuration
- `dev_config` - Development configuration
- `prod_config` - Production configuration

### Backend Fixtures
- `training_manager` - TrainingJobManager instance
- `dataset_manager` - DatasetManager instance

### Model Fixtures
- `sample_training_config` - Sample TrainingConfig
- `sample_dataset_request` - Sample dataset request

### Path Fixtures
- `test_data_dir(tmp_path)` - Temporary data directory
- `test_output_dir(tmp_path)` - Temporary output directory

### Mock Fixtures
- `mock_uds3_strategy` - Mock UDS3 strategy

### Integration Fixtures
- `backend_url` - Dataset backend URL (http://localhost:45681)
- `training_backend_url` - Training backend URL (http://localhost:45680)

## 📝 Writing Tests

### Unit Test Example

```python
# tests/unit/backend/training/test_training_manager.py
import pytest
from backend.training.manager import TrainingJobManager

class TestTrainingJobManager:
    @pytest.fixture
    def manager(self):
        return TrainingJobManager(max_concurrent_jobs=2)
    
    def test_manager_initialization(self, manager):
        assert manager.max_concurrent_jobs == 2
        assert len(manager.jobs) == 0
```

### Integration Test Example

```python
# tests/integration/backend/test_dataset_backend_integration.py
import pytest
import requests

@pytest.mark.integration
class TestDatasetBackend:
    def test_health_endpoint(self, backend_url):
        response = requests.get(f"{backend_url}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

### Using Fixtures

```python
def test_with_config(test_config):
    """Test using config fixture"""
    assert test_config.environment.value == "testing"

def test_with_manager(training_manager, sample_training_config):
    """Test using manager and model fixtures"""
    job = training_manager.create_job(sample_training_config)
    assert job is not None
```

## 🧪 Test Environment

Tests automatically run in testing environment with:
- `CLARA_ENVIRONMENT=testing`
- `CLARA_SECURITY_MODE=testing`
- `CLARA_DEBUG=true`
- `CLARA_JWT_ENABLED=false`
- `UDS3_ENABLED=false`

This is configured in `conftest.py::setup_test_environment()`.

## 📈 Coverage

Run tests with coverage:
```bash
pytest --cov=backend --cov=shared --cov=config --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

## 🔍 Debugging Tests

### Verbose Output
```bash
pytest -v -s
```

### Show Local Variables on Failure
```bash
pytest --showlocals
```

### Drop into Debugger on Failure
```bash
pytest --pdb
```

### Run Only Failed Tests from Last Run
```bash
pytest --lf
```

## 📚 Test Organization Guidelines

### Unit Tests
- **Purpose**: Test individual functions/classes in isolation
- **Speed**: Fast (<100ms per test)
- **Dependencies**: No external services, use mocks
- **Location**: `tests/unit/`

### Integration Tests
- **Purpose**: Test interaction between components
- **Speed**: Medium (100ms-5s per test)
- **Dependencies**: May require backend services running
- **Location**: `tests/integration/`

### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Speed**: Slow (5s+ per test)
- **Dependencies**: All services running
- **Location**: `tests/e2e/`

## 🎯 Current Test Status

### Unit Tests
- ✅ `test_config.py` - Config package tests (18 tests)
- ✅ `test_training_manager.py` - Training manager tests (5 tests)
- ⚠️ `test_dataset_manager.py` - Dataset manager tests (needs update)

### Integration Tests
- ✅ `test_dataset_backend_integration.py` - Dataset backend API tests
- ✅ `test_security_integration.py` - Security integration tests

### Total
- **Unit Tests**: 23+ tests
- **Integration Tests**: 10+ tests
- **Coverage**: ~60% (backend modules)

## 🔄 Next Steps

- [ ] Add unit tests for shared modules (auth, database)
- [ ] Add integration tests for training backend
- [ ] Add end-to-end tests for full workflows
- [ ] Increase test coverage to >80%
- [ ] Add performance benchmarks
- [ ] Add load tests

---

**Updated**: 2025-10-24  
**Test Framework**: pytest 8.4.2  
**Python Version**: 3.13.6
