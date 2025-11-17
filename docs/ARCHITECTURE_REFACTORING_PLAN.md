# Architecture Refactoring Plan - Clean Code Organization

**Status:** ✅ **COMPLETED** (See ARCHITECTURE.md for current production architecture)  
**Original Date:** 2024-10-24  
**Completion Date:** November 2025  
**Original Target:** Clean Architecture, Best Practices, OOP Principles

> **📌 Note:** This document described the refactoring plan. The refactoring has been **fully completed** and the system is now in **production** with clean architecture. For current architecture, see **[ARCHITECTURE.md](./ARCHITECTURE.md)**.

---

## 🎯 Original Goals (All Achieved ✅)

1. ✅ **Separation of Concerns** - Backend, Frontend, Shared modules clearly separated
2. ✅ **Clean Architecture** - Layered design implemented (Presentation, Business Logic, Data)
3. ✅ **OOP Principles** - SOLID, DRY, KISS principles applied throughout
4. ✅ **Testability** - Test structure established
5. ✅ **Maintainability** - Modular structure with clear dependencies
6. ✅ **Scalability** - Microservices architecture implemented

**For current architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md)**

---

## 📊 ORIGINAL STATE (Before Refactoring)

### Original Structure (2024-10-24)

```
Clara/
├── scripts/                      # ❌ Gemischte Backend Services
│   ├── clara_training_backend.py    # Training Service
│   ├── clara_dataset_backend.py     # Dataset Service
│   ├── train_lora.py                # Training Scripts
│   └── migrate_*.py                 # Admin Scripts
├── shared/                       # ⚠️ Flat structure
│   ├── jwt_middleware.py           # Old location
│   └── uds3_dataset_search.py      # Old location
├── tests/                        # ⚠️ Keine Struktur
│   ├── test_training_backend.py
│   └── test_dataset_backend.py
├── docs/                         # ✅ OK
├── data/                         # ✅ OK
└── configs/                      # ⚠️ Gemischt
```

### Probleme

❌ **Backend Services** in `scripts/` statt eigenem Package  
❌ **Shared Modules** ohne Kategorisierung  
❌ **Tests** ohne Unit/Integration/E2E Trennung  
❌ **Config** nicht environment-basiert  
❌ **Keine Frontend-Struktur** (CLI fehlt)  
❌ **Admin Tools** verstreut  
❌ **Imports** teilweise inkonsistent  

---

## 🏗️ SOLL-Zustand (Ziel)

### Clean Architecture Struktur

```
Clara/
├── backend/                      # 🎯 Backend Microservices
│   ├── training/                    # Training Backend Service (45680)
│   │   ├── __init__.py
│   │   ├── app.py                   # FastAPI app entrypoint
│   │   ├── config.py                # Service-specific config
│   │   ├── models.py                # Pydantic models (TrainingJob, etc.)
│   │   ├── manager.py               # TrainingJobManager
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py            # API endpoints
│   │   │   ├── dependencies.py      # FastAPI dependencies
│   │   │   └── websocket.py         # WebSocket handlers
│   │   ├── trainers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # BaseTrainer ABC
│   │   │   ├── lora_trainer.py      # LoRATrainer
│   │   │   ├── qlora_trainer.py     # QLoRATrainer
│   │   │   └── continuous_trainer.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── metrics.py
│   │       └── checkpoint.py
│   │
│   ├── datasets/                    # Dataset Backend Service (45681)
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   ├── models.py                # Dataset, DatasetSearchRequest
│   │   ├── manager.py               # DatasetManager
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py
│   │   ├── quality/
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py          # Quality scoring
│   │   │   └── filters.py
│   │   ├── export/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # BaseExporter ABC
│   │   │   ├── jsonl_exporter.py
│   │   │   ├── parquet_exporter.py
│   │   │   └── csv_exporter.py
│   │   └── utils/
│   │       └── validators.py
│   │
│   ├── serving/                     # Model Serving Service (45682)
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── config.py
│   │   └── models.py
│   │
│   └── common/                      # Shared Backend Utilities
│       ├── __init__.py
│       ├── config.py                # Base backend config
│       ├── exceptions.py            # Custom exceptions
│       ├── logging.py               # Logging setup
│       └── base_service.py          # Base service class
│
├── frontend/                     # 🎨 Frontend Applications
│   ├── cli/                         # CLI Tools
│   │   ├── __init__.py
│   │   ├── training_cli.py          # Training job management
│   │   ├── dataset_cli.py           # Dataset management
│   │   ├── admin_cli.py             # Admin operations
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── formatters.py
│   │       └── validators.py
│   │
│   └── web/                         # Web UI (Future)
│       ├── templates/
│       ├── static/
│       └── components/
│
├── admin/                        # 👨‍💼 Admin Tools
│   ├── scripts/                     # Admin Scripts
│   │   ├── __init__.py
│   │   ├── migrate_sqlite_to_postgres.py
│   │   ├── backup_databases.py
│   │   ├── cleanup_*.py
│   │   └── health_check.py
│   │
│   ├── monitoring/                  # Monitoring Tools
│   │   ├── __init__.py
│   │   ├── metrics_collector.py
│   │   ├── health_checker.py
│   │   └── alert_handler.py
│   │
│   └── deployment/                  # Deployment Tools
│       ├── start_all_services.ps1
│       ├── stop_all_services.ps1
│       ├── start_training_backend.ps1
│       ├── start_dataset_backend.ps1
│       ├── docker/
│       │   ├── Dockerfile.training
│       │   ├── Dockerfile.datasets
│       │   └── docker-compose.yml
│       └── kubernetes/
│           ├── training-deployment.yaml
│           └── dataset-deployment.yaml
│
├── shared/                       # 🔧 Shared Modules
│   ├── auth/                        # Authentication & Authorization
│   │   ├── __init__.py
│   │   ├── middleware.py            # JWT middleware
│   │   ├── models.py                # SecurityConfig, User
│   │   ├── decorators.py            # @require_roles, @optional_auth
│   │   └── utils.py                 # Token helpers
│   │
│   ├── database/                    # Database Clients
│   │   ├── __init__.py
│   │   ├── uds3_client.py           # UDS3 connection manager
│   │   ├── dataset_search.py        # Dataset search API
│   │   └── adapters/
│   │       ├── __init__.py
│   │       ├── postgres.py
│   │       ├── chromadb.py
│   │       └── neo4j.py
│   │
│   ├── models/                      # Shared Pydantic Models
│   │   ├── __init__.py
│   │   ├── base.py                  # Base models
│   │   ├── training.py              # Training-related models
│   │   ├── datasets.py              # Dataset-related models
│   │   └── users.py                 # User models
│   │
│   └── utils/                       # Common Utilities
│       ├── __init__.py
│       ├── validators.py
│       ├── formatters.py
│       ├── helpers.py
│       └── constants.py
│
├── tests/                        # 🧪 Tests
│   ├── unit/                        # Unit Tests
│   │   ├── __init__.py
│   │   ├── backend/
│   │   │   ├── test_training_manager.py
│   │   │   ├── test_dataset_manager.py
│   │   │   └── test_quality_pipeline.py
│   │   ├── shared/
│   │   │   ├── test_auth_middleware.py
│   │   │   └── test_validators.py
│   │   └── conftest.py
│   │
│   ├── integration/                 # Integration Tests
│   │   ├── __init__.py
│   │   ├── test_training_backend.py
│   │   ├── test_dataset_backend.py
│   │   ├── test_security_integration.py
│   │   └── conftest.py
│   │
│   ├── e2e/                         # End-to-End Tests
│   │   ├── __init__.py
│   │   ├── test_full_training_workflow.py
│   │   ├── test_dataset_creation_workflow.py
│   │   └── conftest.py
│   │
│   └── conftest.py                  # Global fixtures
│
├── config/                       # ⚙️ Configuration
│   ├── __init__.py
│   ├── base.py                      # Base config (Pydantic Settings)
│   ├── development.py               # Dev settings
│   ├── production.py                # Prod settings
│   ├── testing.py                   # Test settings
│   └── factory.py                   # Config factory
│
├── docs/                         # 📚 Documentation
│   ├── api/
│   │   ├── training_backend.md
│   │   └── dataset_backend.md
│   ├── architecture/
│   │   ├── overview.md
│   │   ├── backend_services.md
│   │   └── data_flow.md
│   └── guides/
│       ├── quick_start.md
│       └── migration_guide.md
│
├── .env.development              # Environment Files
├── .env.production
├── .env.testing
├── requirements/                 # Requirements Split
│   ├── base.txt
│   ├── dev.txt
│   ├── prod.txt
│   └── test.txt
├── pyproject.toml                # Modern Python Project Config
├── setup.py                      # Package setup
└── README.md                     # Updated README
```

---

## 🔄 Migration Steps

### Phase 1: Backend Services (Priority: HIGH)

#### Step 1.1: Training Backend

**Ziel:** `scripts/clara_training_backend.py` → `backend/training/`

**Aufgaben:**

1. **Package erstellen:**
   ```bash
   mkdir -p backend/training/{api,trainers,utils}
   touch backend/training/__init__.py
   ```

2. **Code aufteilen:**
   - `app.py` - FastAPI app, lifespan
   - `models.py` - TrainingJob, TrainingConfig, Pydantic models
   - `manager.py` - TrainingJobManager class
   - `api/routes.py` - API endpoints
   - `api/websocket.py` - WebSocket handlers
   - `trainers/base.py` - BaseTrainer ABC
   - `trainers/lora_trainer.py` - LoRATrainer
   - `trainers/qlora_trainer.py` - QLoRATrainer

3. **Imports aktualisieren:**
   ```python
   # Vorher
   from shared.jwt_middleware import jwt_middleware
   
   # Nachher
   from shared.auth.middleware import jwt_middleware
   ```

#### Step 1.2: Dataset Backend

**Ziel:** `scripts/clara_dataset_backend.py` → `backend/datasets/`

**Aufgaben:**

1. **Package erstellen:**
   ```bash
   mkdir -p backend/datasets/{api,quality,export,utils}
   ```

2. **Code aufteilen:**
   - `app.py` - FastAPI app
   - `models.py` - Dataset, DatasetSearchRequest
   - `manager.py` - DatasetManager
   - `quality/pipeline.py` - Quality scoring
   - `export/jsonl_exporter.py` - JSONL export
   - `export/parquet_exporter.py` - Parquet export

### Phase 2: Shared Modules (Priority: HIGH)

#### Step 2.1: Auth Module

**Status:** ✅ **COMPLETED** - Files moved to `shared/auth/`

**Original Plan:** `shared/jwt_middleware.py` → `shared/auth/middleware.py`

**Aufgaben:**

1. **Package erstellen:**
   ```bash
   mkdir -p shared/auth
   touch shared/auth/__init__.py
   ```

2. **Code aufteilen:**
   - `middleware.py` - JWTMiddleware class
   - `models.py` - SecurityConfig, User
   - `decorators.py` - require_roles, optional_auth
   - `utils.py` - Token helpers

3. **Exports definieren:**
   ```python
   # shared/auth/__init__.py
   from .middleware import JWTMiddleware, jwt_middleware
   from .decorators import require_roles, optional_auth
   
   __all__ = ['JWTMiddleware', 'jwt_middleware', 'require_roles', 'optional_auth']
   ```

#### Step 2.2: Database Module

**Status:** ✅ **COMPLETED** - Files moved to `shared/database/`

**Original Plan:** `shared/uds3_dataset_search.py` → `shared/database/dataset_search.py`

**Aufgaben:**

1. **Package erstellen:**
   ```bash
   mkdir -p shared/database/adapters
   ```

2. **Code aufteilen:**
   - `uds3_client.py` - Connection manager
   - `dataset_search.py` - DatasetSearchAPI
   - `adapters/postgres.py` - PostgreSQL adapter
   - `adapters/chromadb.py` - ChromaDB adapter
   - `adapters/neo4j.py` - Neo4j adapter

### Phase 3: Frontend & Admin (Priority: MEDIUM)

#### Step 3.1: CLI Tools

**Ziel:** Neue CLI Tools erstellen

**Aufgaben:**

1. **Package erstellen:**
   ```bash
   mkdir -p frontend/cli/utils
   ```

2. **CLI Tools erstellen:**
   - `training_cli.py` - Training job management
   - `dataset_cli.py` - Dataset management
   - `admin_cli.py` - Admin operations

**Beispiel: training_cli.py**
```python
import click
from backend.training.manager import TrainingJobManager

@click.group()
def cli():
    """CLARA Training CLI"""
    pass

@cli.command()
@click.option('--name', required=True)
@click.option('--config', type=click.Path(exists=True))
def create(name, config):
    """Create new training job"""
    # Implementation
    pass

if __name__ == '__main__':
    cli()
```

#### Step 3.2: Admin Tools

**Ziel:** Admin scripts organisieren

**Aufgaben:**

1. **Package erstellen:**
   ```bash
   mkdir -p admin/{scripts,monitoring,deployment}
   ```

2. **Scripts verschieben:**
   - `scripts/migrate_*.py` → `admin/scripts/`
   - `start_*.ps1` → `admin/deployment/`

### Phase 4: Tests (Priority: HIGH)

#### Step 4.1: Test-Struktur

**Ziel:** Tests nach Typ organisieren

**Aufgaben:**

1. **Directories erstellen:**
   ```bash
   mkdir -p tests/{unit,integration,e2e}/{backend,shared,frontend}
   ```

2. **Tests verschieben:**
   - Unit Tests → `tests/unit/backend/test_training_manager.py`
   - Integration Tests → `tests/integration/test_training_backend.py`
   - E2E Tests → `tests/e2e/test_full_workflow.py`

3. **Fixtures organisieren:**
   - Global fixtures → `tests/conftest.py`
   - Unit fixtures → `tests/unit/conftest.py`
   - Integration fixtures → `tests/integration/conftest.py`

### Phase 5: Config Management (Priority: MEDIUM)

#### Step 5.1: Environment-basierte Config

**Ziel:** Pydantic Settings mit .env Files

**Aufgaben:**

1. **Config Package erstellen:**
   ```bash
   mkdir -p config
   touch config/{__init__.py,base.py,development.py,production.py,testing.py,factory.py}
   ```

2. **Base Config erstellen:**
   ```python
   # config/base.py
   from pydantic_settings import BaseSettings
   
   class BaseConfig(BaseSettings):
       # Common settings
       APP_NAME: str = "CLARA"
       DEBUG: bool = False
       
       class Config:
           env_file = ".env"
   ```

3. **Environment Configs:**
   ```python
   # config/development.py
   from .base import BaseConfig
   
   class DevelopmentConfig(BaseConfig):
       DEBUG: bool = True
       CLARA_SECURITY_MODE: str = "development"
   ```

4. **Config Factory:**
   ```python
   # config/factory.py
   import os
   from .development import DevelopmentConfig
   from .production import ProductionConfig
   from .testing import TestingConfig
   
   def get_config():
       env = os.environ.get('CLARA_ENV', 'development')
       
       configs = {
           'development': DevelopmentConfig,
           'production': ProductionConfig,
           'testing': TestingConfig
       }
       
       return configs[env]()
   ```

---

## 🔧 Implementation Details

### OOP Principles

#### 1. Single Responsibility Principle (SRP)

**Vorher (Monolithic):**
```python
# clara_training_backend.py (900 Zeilen)
class TrainingJobManager:
    def create_job(self): ...
    def run_training(self): ...
    def _run_lora_training(self): ...
    def _run_qlora_training(self): ...
    def _export_metrics(self): ...
```

**Nachher (Modular):**
```python
# backend/training/manager.py
class TrainingJobManager:
    def create_job(self): ...
    def run_job(self): ...

# backend/training/trainers/lora_trainer.py
class LoRATrainer(BaseTrainer):
    def train(self): ...

# backend/training/utils/metrics.py
class MetricsExporter:
    def export(self): ...
```

#### 2. Open/Closed Principle (OCP)

**Base Trainer ABC:**
```python
# backend/training/trainers/base.py
from abc import ABC, abstractmethod

class BaseTrainer(ABC):
    @abstractmethod
    def train(self, config: TrainingConfig) -> TrainingResult:
        """Train model with given config"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate training setup"""
        pass

# backend/training/trainers/lora_trainer.py
class LoRATrainer(BaseTrainer):
    def train(self, config: TrainingConfig) -> TrainingResult:
        # LoRA-specific implementation
        pass
```

#### 3. Dependency Inversion Principle (DIP)

**Interfaces statt Konkrete Klassen:**
```python
# backend/datasets/export/base.py
class BaseExporter(ABC):
    @abstractmethod
    def export(self, data: List[DatasetDocument]) -> Path:
        pass

# backend/datasets/manager.py
class DatasetManager:
    def __init__(self, exporter: BaseExporter):
        self.exporter = exporter  # Dependency injection
```

---

## 📦 Package Structure Best Practices

### __init__.py Pattern

```python
# backend/training/__init__.py
"""
Training Backend Service

Exports:
- app: FastAPI application
- TrainingJobManager: Job management
- TrainingJob: Job model
"""

from .app import app
from .manager import TrainingJobManager
from .models import TrainingJob, TrainingConfig

__version__ = "1.0.0"
__all__ = [
    'app',
    'TrainingJobManager',
    'TrainingJob',
    'TrainingConfig'
]
```

### Relative vs Absolute Imports

**Relative Imports (innerhalb Package):**
```python
# backend/training/api/routes.py
from ..models import TrainingJob
from ..manager import TrainingJobManager
```

**Absolute Imports (zwischen Packages):**
```python
# backend/training/app.py
from shared.auth.middleware import jwt_middleware
from shared.database.uds3_client import UDS3Client
from backend.common.logging import setup_logger
```

---

## 🧪 Testing Strategy

### Unit Tests

**Ziel:** Isolierte Komponenten testen

```python
# tests/unit/backend/test_training_manager.py
import pytest
from backend.training.manager import TrainingJobManager
from backend.training.models import TrainingJob

def test_create_job():
    manager = TrainingJobManager()
    job = manager.create_job(
        name="Test Job",
        trainer_type="lora",
        config={}
    )
    
    assert job.status == "pending"
    assert job.trainer_type == "lora"
```

### Integration Tests

**Ziel:** API Endpoints testen

```python
# tests/integration/test_training_backend.py
import pytest
from fastapi.testclient import TestClient
from backend.training.app import app

@pytest.fixture
def client():
    return TestClient(app)

def test_create_training_job(client):
    response = client.post("/api/training/jobs", json={
        "job_name": "Test",
        "trainer_type": "lora",
        "config": {}
    })
    
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### E2E Tests

**Ziel:** Komplette Workflows testen

```python
# tests/e2e/test_full_training_workflow.py
def test_full_training_workflow(client):
    # 1. Create dataset
    dataset_response = client.post("/api/datasets", ...)
    dataset_id = dataset_response.json()["dataset_id"]
    
    # 2. Create training job
    job_response = client.post("/api/training/jobs", ...)
    job_id = job_response.json()["job_id"]
    
    # 3. Wait for completion
    # ...
    
    # 4. Verify results
    assert job.status == "completed"
```

---

## 📋 Checklist

### Pre-Migration

- [ ] Backup aktueller Code (`git branch backup-before-refactor`)
- [ ] Alle Tests laufen grün
- [ ] Services laufen erfolgreich
- [ ] Dependencies dokumentiert

### Migration Phase 1: Backend

- [ ] `backend/training/` Package erstellt
- [ ] `backend/datasets/` Package erstellt
- [ ] `backend/common/` Package erstellt
- [ ] Code aufgeteilt und refactored
- [ ] __init__.py Files erstellt
- [ ] Imports aktualisiert

### Migration Phase 2: Shared

- [ ] `shared/auth/` Package erstellt
- [ ] `shared/database/` Package erstellt
- [ ] `shared/models/` Package erstellt
- [ ] `shared/utils/` Package erstellt
- [ ] Exports definiert (__all__)

### Migration Phase 3: Frontend & Admin

- [ ] `frontend/cli/` Package erstellt
- [ ] CLI Tools implementiert
- [ ] `admin/scripts/` organisiert
- [ ] `admin/deployment/` organisiert

### Migration Phase 4: Tests

- [ ] `tests/unit/` Struktur erstellt
- [ ] `tests/integration/` Struktur erstellt
- [ ] `tests/e2e/` Struktur erstellt
- [ ] Fixtures organisiert
- [ ] Alle Tests migriert

### Migration Phase 5: Config

- [ ] `config/` Package erstellt
- [ ] Environment configs implementiert
- [ ] .env Files erstellt
- [ ] Config factory implementiert

### Post-Migration

- [ ] Alle Imports funktionieren
- [ ] Alle Services starten
- [ ] Alle Tests laufen grün
- [ ] Linting clean (ruff, black, mypy)
- [ ] Documentation aktualisiert
- [ ] Migration Guide erstellt
- [ ] Git commit mit aussagekräftiger Message

---

## 🚀 Deployment Strategy

### Local Development

```bash
# Set environment
export CLARA_ENV=development

# Start services
python -m backend.training.app
python -m backend.datasets.app
```

### Docker

```dockerfile
# Dockerfile.training
FROM python:3.9-slim

WORKDIR /app
COPY requirements/base.txt requirements/prod.txt ./
RUN pip install -r prod.txt

COPY backend/training/ ./backend/training/
COPY shared/ ./shared/
COPY config/ ./config/

ENV CLARA_ENV=production
CMD ["python", "-m", "backend.training.app"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  training-backend:
    build:
      context: .
      dockerfile: admin/deployment/docker/Dockerfile.training
    ports:
      - "45680:45680"
    environment:
      - CLARA_ENV=production
    
  dataset-backend:
    build:
      context: .
      dockerfile: admin/deployment/docker/Dockerfile.datasets
    ports:
      - "45681:45681"
```

---

## 📈 Benefits Achieved

### Before Refactoring (Monolithic)

❌ 900-line files  
❌ Mixed concerns  
❌ Hard to test  
❌ Hard to maintain  
❌ No clear structure  

### After Refactoring (Clean Architecture) ✅

✅ **Modular Structure** - Clear separation achieved  
✅ **Testable** - Test infrastructure established  
✅ **Maintainable** - Small, focused modules  
✅ **Scalable** - Microservices architecture implemented  
✅ **Professional** - Industry best practices applied  
✅ **OOP Principles** - SOLID, DRY, KISS throughout  

---

## ✅ IMPLEMENTATION COMPLETE (November 2025)

**Refactoring successfully completed!**

### What Was Achieved

1. ✅ **Backend Microservices** - Training (45680), Dataset (45681)
2. ✅ **Frontend Applications** - 3 separate tkinter GUIs
3. ✅ **Shared Modules** - Hierarchical structure (auth/, database/)
4. ✅ **Configuration System** - Pydantic-based centralized config
5. ✅ **Security Framework** - JWT with 4 security modes
6. ✅ **Clean Architecture** - Layered design implemented

### Current Production Architecture

For detailed information about the current system architecture, see:

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete architecture overview
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Current implementation status
- **[IMPLEMENTATION_HISTORY.md](./IMPLEMENTATION_HISTORY.md)** - Implementation timeline

---

## 📚 References

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Python Package Structure Best Practices](https://docs.python-guide.org/writing/structure/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [12-Factor App](https://12factor.net/)

---

**Original Status:** 📋 PLANNING (Oct 2024)  
**Final Status:** ✅ **COMPLETED** (Nov 2025)  
**Implementation Time:** ~20 hours across multiple phases  
**Result:** Clean, maintainable, production-ready architecture
