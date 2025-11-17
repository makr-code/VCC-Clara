# Clara Testing Guide

Complete guide to testing the Clara AI system, including unit tests, integration tests, and end-to-end tests.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Fixtures](#test-fixtures)
6. [Test Markers](#test-markers)
7. [Test Environment](#test-environment)
8. [Code Coverage](#code-coverage)
9. [Debugging Tests](#debugging-tests)
10. [Best Practices](#best-practices)
11. [CI/CD Integration](#cicd-integration)
12. [Troubleshooting](#troubleshooting)

---

## Overview

Clara uses **pytest** as the testing framework with a comprehensive test suite covering:

- **Unit Tests**: Fast, isolated tests for individual functions/classes
- **Integration Tests**: Tests for component interactions (require services)
- **End-to-End Tests**: Complete workflow tests (all services running)

**Test Framework**: pytest 8.4.2  
**Python Version**: 3.13.6  
**Current Coverage**: ~60% (backend modules)  
**Total Tests**: 33+ tests (23 unit, 10+ integration)

---

## Test Structure

### Directory Organization

```
tests/
├── conftest.py                 # Global pytest configuration and fixtures
├── pytest.ini                  # Pytest settings
├── README.md                   # Test documentation
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

### Test Types

| Type | Purpose | Speed | Dependencies | Location |
|------|---------|-------|--------------|----------|
| **Unit** | Test individual functions/classes | Fast (<100ms) | None (mocked) | `tests/unit/` |
| **Integration** | Test component interactions | Medium (100ms-5s) | Services running | `tests/integration/` |
| **E2E** | Test complete workflows | Slow (5s+) | All services | `tests/e2e/` |

---

## Running Tests

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies (if not in requirements.txt)
pip install pytest pytest-asyncio pytest-cov
```

### Basic Commands

```bash
# Run all tests
pytest

# Run all tests with verbose output
pytest -v

# Run tests and show print statements
pytest -v -s

# Run specific test directory
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/config/test_config.py -v

# Run specific test class
pytest tests/unit/config/test_config.py::TestBaseConfig -v

# Run specific test method
pytest tests/unit/config/test_config.py::TestBaseConfig::test_default_config_loads -v
```

### Running by Marker

```bash
# Unit tests only
pytest -m unit -v

# Integration tests only
pytest -m integration -v

# End-to-end tests only
pytest -m e2e -v

# Exclude slow tests
pytest -m "not slow" -v

# Run unit OR integration tests
pytest -m "unit or integration" -v
```

### Running by Keyword

```bash
# All tests with "config" in name
pytest -k "config" -v

# All tests starting with "test_create"
pytest -k "test_create" -v

# All tests with "manager" in name
pytest -k "manager" -v

# Complex keyword expressions
pytest -k "config and not slow" -v
```

### PowerShell Script (Windows)

```powershell
# Create run_tests.ps1
# Run all tests
python -m pytest tests/ -v

# Run unit tests only
python -m pytest tests/unit/ -v -m unit

# Run integration tests (requires services)
# Start services first
.\start_backends.ps1
Start-Sleep -Seconds 5
python -m pytest tests/integration/ -v -m integration

# Stop services
.\stop_backends.ps1
```

### Bash Script (Linux/macOS)

```bash
#!/bin/bash
# run_tests.sh

# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v -m unit

# Run integration tests (requires services)
# Start services first
python -m backend.training.app &
TRAINING_PID=$!
python -m backend.datasets.app &
DATASET_PID=$!

sleep 5
pytest tests/integration/ -v -m integration

# Stop services
kill $TRAINING_PID $DATASET_PID
```

---

## Writing Tests

### Unit Test Example

```python
# tests/unit/backend/training/test_training_manager.py
import pytest
from unittest.mock import Mock, patch
from backend.training.manager import TrainingJobManager
from backend.training.models import TrainingJobRequest, TrainerType

class TestTrainingJobManager:
    """Test TrainingJobManager class"""
    
    @pytest.fixture
    def manager(self):
        """Create a TrainingJobManager instance for testing"""
        return TrainingJobManager(max_concurrent_jobs=2)
    
    def test_manager_initialization(self, manager):
        """Test manager initializes with correct defaults"""
        assert manager.max_concurrent_jobs == 2
        assert len(manager.jobs) == 0
    
    def test_create_job(self, manager):
        """Test job creation returns valid job"""
        job_request = TrainingJobRequest(
            trainer_type=TrainerType.LORA,
            config_path="test-config.yaml",
            dataset_path="test-data.jsonl",
            priority=1
        )
        
        job = manager.create_job(job_request, user_email="test@example.com")
        
        assert job.job_id is not None
        assert job.status == "pending"
        assert job.trainer_type == TrainerType.LORA
        assert job.job_id in manager.jobs
```

### Integration Test Example

```python
# tests/integration/backend/test_dataset_backend_integration.py
import pytest
import requests

@pytest.mark.integration
class TestDatasetBackendAPI:
    """Integration tests for Dataset Backend API"""
    
    def test_health_endpoint(self, backend_url):
        """Test /health endpoint returns healthy status"""
        response = requests.get(f"{backend_url}/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_create_dataset(self, backend_url):
        """Test dataset creation via API"""
        payload = {
            "name": "Test Dataset",
            "search_query": "compliance",
            "export_formats": ["jsonl", "parquet"]
        }
        
        response = requests.post(
            f"{backend_url}/api/datasets",
            json=payload
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "dataset_id" in data
        assert data["name"] == "Test Dataset"
```

### Async Test Example

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await some_async_function()
    assert result is not None
```

### Using Mocks

```python
from unittest.mock import Mock, patch, AsyncMock

def test_with_mock():
    """Test using mocks"""
    # Create a mock object
    mock_database = Mock()
    mock_database.query.return_value = [{"id": 1, "name": "Test"}]
    
    # Use the mock
    result = mock_database.query("SELECT * FROM test")
    assert len(result) == 1
    
    # Verify mock was called
    mock_database.query.assert_called_once_with("SELECT * FROM test")

@patch('backend.training.manager.TrainerFactory')
def test_with_patch(mock_factory):
    """Test using patches"""
    mock_factory.create_trainer.return_value = Mock()
    
    manager = TrainingJobManager()
    trainer = manager.get_trainer("lora")
    
    mock_factory.create_trainer.assert_called_once()
```

### Parametrized Tests

```python
@pytest.mark.parametrize("trainer_type,expected_class", [
    ("lora", LoRATrainer),
    ("full", FullTrainer),
    ("qlora", QLoRATrainer),
])
def test_trainer_factory(trainer_type, expected_class):
    """Test trainer factory creates correct trainer types"""
    trainer = TrainerFactory.create_trainer(trainer_type)
    assert isinstance(trainer, expected_class)

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    """Test doubling function"""
    assert double(input) == expected
```

---

## Test Fixtures

### Available Fixtures (from conftest.py)

#### Config Fixtures

```python
def test_with_test_config(test_config):
    """Test using testing configuration"""
    assert test_config.environment.value == "testing"
    assert test_config.debug is True

def test_with_dev_config(dev_config):
    """Test using development configuration"""
    assert dev_config.environment.value == "development"

def test_with_prod_config(prod_config):
    """Test using production configuration"""
    assert prod_config.environment.value == "production"
```

#### Backend Fixtures

```python
def test_with_training_manager(training_manager):
    """Test using TrainingJobManager fixture"""
    assert training_manager.max_concurrent_jobs > 0

def test_with_dataset_manager(dataset_manager):
    """Test using DatasetManager fixture"""
    assert dataset_manager is not None
```

#### Model Fixtures

```python
def test_with_sample_config(sample_training_config):
    """Test using sample training config"""
    assert sample_training_config.trainer_type == TrainerType.LORA

def test_with_sample_request(sample_dataset_request):
    """Test using sample dataset request"""
    assert sample_dataset_request.name == "Test Dataset"
```

#### Path Fixtures

```python
def test_with_temp_dir(test_data_dir):
    """Test using temporary data directory"""
    # test_data_dir is a Path object pointing to tmp directory
    test_file = test_data_dir / "test.txt"
    test_file.write_text("test content")
    assert test_file.exists()

def test_with_output_dir(test_output_dir):
    """Test using temporary output directory"""
    output_file = test_output_dir / "output.jsonl"
    # File cleanup happens automatically after test
```

#### Integration Fixtures

```python
@pytest.mark.integration
def test_with_backend_urls(backend_url, training_backend_url):
    """Test using backend URL fixtures"""
    # backend_url = "http://localhost:45681"
    # training_backend_url = "http://localhost:45680"
    response = requests.get(f"{backend_url}/health")
    assert response.status_code == 200
```

### Creating Custom Fixtures

```python
# In your test file
@pytest.fixture
def custom_manager():
    """Create a custom manager with specific settings"""
    manager = TrainingJobManager(max_concurrent_jobs=5)
    yield manager
    # Cleanup code here (if needed)
    manager.cleanup()

@pytest.fixture(scope="module")
def database_connection():
    """Module-scoped fixture (setup once per test file)"""
    conn = create_database_connection()
    yield conn
    conn.close()

@pytest.fixture(scope="session")
def test_server():
    """Session-scoped fixture (setup once per test run)"""
    server = start_test_server()
    yield server
    server.stop()
```

---

## Test Markers

### Built-in Markers

```python
@pytest.mark.unit
def test_unit_example():
    """Unit test marker"""
    pass

@pytest.mark.integration
def test_integration_example():
    """Integration test marker (requires services)"""
    pass

@pytest.mark.e2e
def test_e2e_example():
    """End-to-end test marker (full workflow)"""
    pass

@pytest.mark.slow
def test_slow_example():
    """Slow test marker (takes >1 second)"""
    import time
    time.sleep(2)

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    """Skip this test"""
    pass

@pytest.mark.skipif(sys.platform == "win32", reason="Unix only")
def test_unix_only():
    """Skip on Windows"""
    pass

@pytest.mark.xfail(reason="Known bug")
def test_known_issue():
    """Expected to fail"""
    assert False
```

### Custom Markers

```python
# In pytest.ini
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    security: Security-related tests
    database: Database tests

# In test file
@pytest.mark.security
def test_jwt_validation():
    """Security test"""
    pass

@pytest.mark.database
def test_database_query():
    """Database test"""
    pass
```

---

## Test Environment

### Environment Variables

Tests automatically run with testing configuration:

```bash
CLARA_ENVIRONMENT=testing
CLARA_SECURITY_MODE=testing
CLARA_DEBUG=true
CLARA_JWT_ENABLED=false
UDS3_ENABLED=false
CLARA_TRAINING_PORT=45680
CLARA_DATASET_PORT=45681
```

### Setting Environment in Tests

```python
import os
import pytest

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set environment variables for all tests"""
    monkeypatch.setenv("CLARA_ENVIRONMENT", "testing")
    monkeypatch.setenv("CLARA_DEBUG", "true")

def test_with_custom_env(monkeypatch):
    """Test with custom environment variable"""
    monkeypatch.setenv("CUSTOM_VAR", "test_value")
    assert os.getenv("CUSTOM_VAR") == "test_value"
```

### Test Configuration

```python
# conftest.py
@pytest.fixture(scope="session")
def setup_test_environment():
    """Setup test environment before any tests run"""
    os.environ["CLARA_ENVIRONMENT"] = "testing"
    os.environ["CLARA_SECURITY_MODE"] = "testing"
    os.environ["CLARA_DEBUG"] = "true"
    yield
    # Cleanup after all tests
```

---

## Code Coverage

### Running with Coverage

```bash
# Run all tests with coverage
pytest --cov=backend --cov=shared --cov=config

# Generate HTML report
pytest --cov=backend --cov=shared --cov=config --cov-report=html

# Show missing lines in terminal
pytest --cov=backend --cov-report=term-missing

# Generate both HTML and terminal reports
pytest --cov=backend --cov=shared --cov=config \
    --cov-report=html \
    --cov-report=term-missing
```

### Viewing Coverage Report

```bash
# Open HTML report (macOS/Linux)
open htmlcov/index.html

# Open HTML report (Windows PowerShell)
Start-Process htmlcov/index.html

# Open HTML report (Windows Command Prompt)
start htmlcov\index.html
```

### Coverage Configuration

```ini
# In pytest.ini or setup.cfg
[tool:pytest]
addopts = 
    --cov=backend
    --cov=shared
    --cov=config
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

### Coverage Targets

| Component | Current | Target |
|-----------|---------|--------|
| backend/training | ~70% | >85% |
| backend/datasets | ~60% | >85% |
| shared/auth | ~50% | >80% |
| shared/database | ~40% | >80% |
| config | ~80% | >90% |
| **Overall** | **~60%** | **>80%** |

---

## Debugging Tests

### Verbose Output

```bash
# Show test names and results
pytest -v

# Show print statements
pytest -v -s

# Show local variables on failure
pytest --showlocals

# Show full traceback
pytest --tb=long

# Show short traceback (default)
pytest --tb=short

# Show no traceback
pytest --tb=no
```

### Interactive Debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on error (not failure)
pytest --pdb-trace

# Drop into debugger at start of each test
pytest --trace
```

### Debugging Specific Tests

```python
def test_with_breakpoint():
    """Test with Python breakpoint"""
    x = 10
    breakpoint()  # Execution pauses here
    y = x * 2
    assert y == 20

def test_with_pdb():
    """Test with pdb"""
    import pdb
    x = 10
    pdb.set_trace()  # Execution pauses here
    y = x * 2
    assert y == 20
```

### Running Failed Tests

```bash
# Run only tests that failed in last run
pytest --lf

# Run failed tests first, then others
pytest --ff

# Run tests in the order they last failed
pytest --failed-first
```

### Logging Output

```python
import logging

def test_with_logging(caplog):
    """Test with logging capture"""
    logger = logging.getLogger(__name__)
    logger.info("Test message")
    
    assert "Test message" in caplog.text
    
    # Check log level
    assert caplog.records[0].levelname == "INFO"
```

---

## Best Practices

### Test Organization

1. **One test file per module**
   ```
   backend/training/manager.py → tests/unit/backend/training/test_manager.py
   ```

2. **One test class per class**
   ```python
   class TestTrainingJobManager:
       """Tests for TrainingJobManager"""
   ```

3. **Descriptive test names**
   ```python
   def test_create_job_returns_valid_job_id():  # Good
   def test1():  # Bad
   ```

4. **Arrange-Act-Assert pattern**
   ```python
   def test_create_job():
       # Arrange
       manager = TrainingJobManager()
       request = TrainingJobRequest(...)
       
       # Act
       job = manager.create_job(request)
       
       # Assert
       assert job.job_id is not None
   ```

### Test Independence

```python
# Good: Tests are independent
def test_create_job():
    manager = TrainingJobManager()
    job = manager.create_job(...)
    assert job.job_id is not None

def test_get_job():
    manager = TrainingJobManager()
    job = manager.create_job(...)
    retrieved = manager.get_job(job.job_id)
    assert retrieved == job

# Bad: Tests depend on each other
job_id = None

def test_create_job():
    global job_id
    manager = TrainingJobManager()
    job = manager.create_job(...)
    job_id = job.job_id  # Don't do this

def test_get_job():
    global job_id
    manager = TrainingJobManager()
    job = manager.get_job(job_id)  # Depends on previous test
```

### Testing Edge Cases

```python
def test_create_job_with_valid_input():
    """Test normal case"""
    pass

def test_create_job_with_invalid_trainer_type():
    """Test with invalid input"""
    with pytest.raises(ValueError):
        manager.create_job(invalid_request)

def test_create_job_with_missing_config_path():
    """Test with missing required field"""
    with pytest.raises(ValidationError):
        manager.create_job(incomplete_request)

def test_create_job_with_none():
    """Test with None input"""
    with pytest.raises(TypeError):
        manager.create_job(None)

def test_create_job_with_empty_string():
    """Test with empty string"""
    pass
```

### Mocking Best Practices

```python
# Good: Mock external dependencies
@patch('requests.get')
def test_api_call(mock_get):
    mock_get.return_value.status_code = 200
    result = call_external_api()
    assert result is not None

# Bad: Don't mock what you're testing
@patch('backend.training.manager.TrainingJobManager.create_job')
def test_create_job(mock_create):  # Don't mock your own code
    pass
```

### Assertion Best Practices

```python
# Good: Specific assertions
assert job.status == JobStatus.PENDING
assert len(jobs) == 3
assert "error" in response.json()

# Bad: Generic assertions
assert job  # What are we checking?
assert response  # Too vague
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run unit tests
      run: pytest tests/unit/ -v -m unit
    
    - name: Run integration tests
      run: |
        # Start services
        python -m backend.training.app &
        python -m backend.datasets.app &
        sleep 10
        
        # Run tests
        pytest tests/integration/ -v -m integration
        
        # Stop services
        pkill -f backend.training.app
        pkill -f backend.datasets.app
    
    - name: Generate coverage report
      run: |
        pytest --cov=backend --cov=shared --cov=config \
          --cov-report=xml --cov-report=term
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash

echo "Running tests before commit..."
pytest tests/unit/ -v -m unit

if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi

echo "All tests passed!"
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Problem
ModuleNotFoundError: No module named 'backend'

# Solution
# Ensure pytest.ini has correct pythonpath
[pytest]
pythonpath = src

# Or set PYTHONPATH before running tests
export PYTHONPATH=/path/to/VCC-Clara:$PYTHONPATH  # Linux/macOS
$env:PYTHONPATH = "C:\path\to\VCC-Clara;$env:PYTHONPATH"  # PowerShell
```

#### 2. Integration Tests Fail

```bash
# Problem
ConnectionError: Failed to connect to backend

# Solution
# Ensure services are running
python -m backend.training.app &
python -m backend.datasets.app &

# Wait for services to start
sleep 5

# Run integration tests
pytest tests/integration/ -v -m integration
```

#### 3. Async Tests Not Running

```bash
# Problem
PytestUnraisableExceptionWarning: Async test not awaited

# Solution
# Install pytest-asyncio
pip install pytest-asyncio

# Mark async tests
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

#### 4. Fixtures Not Found

```bash
# Problem
fixture 'test_config' not found

# Solution
# Ensure conftest.py is in correct location
tests/conftest.py  # Global fixtures
tests/unit/conftest.py  # Unit test fixtures
tests/integration/conftest.py  # Integration test fixtures
```

#### 5. Slow Tests

```bash
# Problem
Tests take too long

# Solution
# Run only fast tests
pytest -m "not slow" -v

# Run tests in parallel
pip install pytest-xdist
pytest -n auto  # Use all CPU cores
pytest -n 4     # Use 4 workers
```

### Getting Help

```bash
# Show pytest help
pytest --help

# Show available fixtures
pytest --fixtures

# Show available markers
pytest --markers

# Show test collection (don't run)
pytest --collect-only

# Show why tests were selected/deselected
pytest -v -r a
```

---

## Summary

### Quick Reference

| Task | Command |
|------|---------|
| Run all tests | `pytest` |
| Run unit tests | `pytest -m unit` |
| Run integration tests | `pytest -m integration` |
| Run with coverage | `pytest --cov=backend --cov-report=html` |
| Run specific file | `pytest tests/unit/config/test_config.py` |
| Debug test | `pytest --pdb` |
| Run failed tests | `pytest --lf` |
| Show fixtures | `pytest --fixtures` |
| Verbose output | `pytest -v -s` |

### Test Checklist

- [ ] Tests are independent (don't rely on order)
- [ ] Tests have descriptive names
- [ ] Tests use Arrange-Act-Assert pattern
- [ ] Edge cases are tested
- [ ] Appropriate markers are used
- [ ] External dependencies are mocked
- [ ] Tests run in <100ms (unit tests)
- [ ] Code coverage >80%
- [ ] Tests pass in CI/CD

---

**Last Updated**: 2025-11-17  
**Test Framework**: pytest 8.4.2  
**Python Version**: 3.13.6  
**Current Test Count**: 33+ tests  
**Current Coverage**: ~60%  
**Target Coverage**: >80%
