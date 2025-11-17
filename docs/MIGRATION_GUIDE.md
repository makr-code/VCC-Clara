# Migration Guide: Clean Architecture Refactoring

**Version:** 1.0  
**Date:** 2024-10-24  
**Estimated Time:** 8-12 hours (can be done in phases)

---

## 🎯 Overview

This guide walks you through migrating the Clara codebase from a **flat monolithic structure** to a **Clean Architecture** with proper separation of concerns.

### What Changes

**Before:**
```
scripts/         # 102 files - everything mixed
shared/          # 2 files - too flat
tests/           # 9 files - no organization
```

**After:**
```
backend/         # Microservices (training, datasets, serving)
shared/          # Organized (auth/, database/, models/, utils/)
tests/           # Structured (unit/, integration/, e2e/)
admin/           # Tools (scripts/, monitoring/, deployment/)
frontend/        # CLI tools, future web UI
config/          # Environment-based configuration
```

---

## ⚠️ Prerequisites

1. **Backup Everything:**
   ```bash
   git checkout -b backup-before-refactor
   git push origin backup-before-refactor
   ```

2. **Run Baseline Tests:**
   ```bash
   pytest tests/ -v > baseline_tests.txt
   ```

3. **Document Current Services:**
   ```bash
   # Test that services start
   python scripts/clara_training_backend.py &
   python scripts/clara_dataset_backend.py &
   # Kill after verification
   ```

---

## 📦 Phase 1: Backend Services (4-5 hours)

### Step 1.1: Create Backend Structure

```bash
mkdir -p backend/training/{api,trainers,utils}
mkdir -p backend/datasets/{api,quality,export,utils}
mkdir -p backend/common
```

### Step 1.2: Refactor Training Backend

**File:** `scripts/clara_training_backend.py` (993 lines) → Multiple modules

#### Create `backend/training/models.py`

**Extract:** All model classes (lines 90-180 approx)
- `JobStatus` enum
- `TrainerType` enum
- `TrainingJob` dataclass
- `TrainingJobRequest`, `TrainingJobResponse`, `JobListResponse`, `JobUpdateMessage`

```bash
# Copy from scripts/clara_training_backend.py lines 90-180
# to backend/training/models.py
```

✅ **Already created:** `backend/training/models.py`

#### Create `backend/training/manager.py`

**Extract:** `TrainingJobManager` class (lines 185-580 approx)

```python
# backend/training/manager.py
"""Training Job Manager with Worker Pool"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from .models import TrainingJob, JobStatus, TrainerType
from .trainers.base import BaseTrainer
from .trainers.lora_trainer import LoRATrainer
from .trainers.qlora_trainer import QLoRATrainer

logger = logging.getLogger(__name__)


class TrainingJobManager:
    """Job Manager - copy from clara_training_backend.py lines ~220-570"""
    
    def __init__(self, max_concurrent_jobs: int = 2):
        self.jobs: Dict[str, TrainingJob] = {}
        self.max_concurrent_jobs = max_concurrent_jobs
        # ... rest of __init__
    
    # Copy all methods from TrainingJobManager class
    # - start_workers()
    # - stop_workers()
    # - create_job()
    # - submit_job()
    # - _worker()
    # - _execute_job()
    # - _run_training()
    # - get_job()
    # - list_jobs()
    # - cancel_job()
    # - etc.
```

#### Create `backend/training/trainers/base.py`

```python
# backend/training/trainers/base.py
"""Base Trainer Abstract Class"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path


class BaseTrainer(ABC):
    """Base class for all trainers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get("training", {}).get("output_dir", "models/outputs"))
    
    @abstractmethod
    def train(self) -> Dict[str, Any]:
        """
        Train model and return results
        
        Returns:
            Dictionary with:
            - adapter_path: str - Path to trained adapter
            - metrics: Dict[str, float] - Training metrics
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate training setup before starting"""
        pass
```

#### Create `backend/training/trainers/lora_trainer.py`

```python
# backend/training/trainers/lora_trainer.py
"""LoRA Trainer Implementation"""

import logging
from typing import Dict, Any
from pathlib import Path

from .base import BaseTrainer

logger = logging.getLogger(__name__)


class LoRATrainer(BaseTrainer):
    """LoRA Training Implementation"""
    
    def validate(self) -> bool:
        """Validate LoRA config"""
        required = ["model_name", "dataset_path", "num_epochs"]
        training_config = self.config.get("training", {})
        
        for key in required:
            if key not in training_config:
                logger.error(f"Missing required config: {key}")
                return False
        
        return True
    
    def train(self) -> Dict[str, Any]:
        """Run LoRA training"""
        logger.info("🚀 Starting LoRA Training")
        
        if not self.validate():
            raise ValueError("Invalid LoRA configuration")
        
        # TODO: Integrate with scripts/clara_train_lora.py
        # For now: simulation
        logger.warning("⚠️ Using simulated training (TODO: integrate real trainer)")
        
        return self._simulate_training()
    
    def _simulate_training(self) -> Dict[str, Any]:
        """Simulate training for development"""
        import time
        
        num_epochs = self.config.get("training", {}).get("num_epochs", 3)
        
        for epoch in range(1, num_epochs + 1):
            logger.info(f"  Epoch {epoch}/{num_epochs}")
            time.sleep(1)
        
        adapter_path = self.output_dir / "adapter_model"
        
        return {
            "adapter_path": str(adapter_path),
            "metrics": {
                "final_loss": 0.25,
                "perplexity": 10.5,
                "accuracy": 0.85
            }
        }
```

#### Create `backend/training/api/routes.py`

**Extract:** All @app.* decorated functions (API endpoints)

```python
# backend/training/api/routes.py
"""Training API Routes"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, WebSocket
from typing import Optional

from ..models import (
    TrainingJobRequest,
    TrainingJobResponse,
    JobListResponse,
    JobStatus
)
from ..manager import TrainingJobManager

# Import from shared (will be refactored later)
from shared.auth.middleware import jwt_middleware, get_current_user_email

router = APIRouter(prefix="/api/training", tags=["training"])

# Global manager (will be injected via dependency)
job_manager: Optional[TrainingJobManager] = None


def get_job_manager() -> TrainingJobManager:
    """Dependency for job manager"""
    if job_manager is None:
        raise HTTPException(status_code=503, detail="Job Manager not initialized")
    return job_manager


@router.post("/jobs", response_model=TrainingJobResponse)
async def create_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks,
    manager: TrainingJobManager = Depends(get_job_manager),
    user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer"]))
):
    """Create new training job"""
    # Copy implementation from clara_training_backend.py
    pass


@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(
    job_id: str,
    manager: TrainingJobManager = Depends(get_job_manager),
    user: dict = Depends(jwt_middleware.get_current_user)
):
    """Get job details"""
    # Copy implementation
    pass


# ... more endpoints
```

#### Create `backend/training/app.py`

**Extract:** FastAPI app initialization, lifespan, main

```python
# backend/training/app.py
"""Training Backend FastAPI Application"""

import os
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .manager import TrainingJobManager
from .api import routes

logger = logging.getLogger(__name__)

SERVICE_PORT = int(os.environ.get("CLARA_TRAINING_PORT", "45680"))
MAX_CONCURRENT_JOBS = int(os.environ.get("CLARA_MAX_CONCURRENT_JOBS", "2"))

# Global manager
job_manager: Optional[TrainingJobManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Lifespan"""
    global job_manager
    
    # Startup
    logger.info("🚀 Training Backend startet...")
    job_manager = TrainingJobManager(max_concurrent_jobs=MAX_CONCURRENT_JOBS)
    await job_manager.start_workers()
    
    # Inject into routes
    routes.job_manager = job_manager
    
    logger.info(f"✅ Training Backend bereit (Port {SERVICE_PORT})")
    
    yield
    
    # Shutdown
    logger.info("🛑 Training Backend wird gestoppt...")
    await job_manager.stop_workers()


app = FastAPI(
    title="CLARA Training Backend",
    description="Microservice für LoRa/QLoRa Training Management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router)


@app.get("/health")
async def health_check():
    """Health Check"""
    return {
        "status": "healthy",
        "service": "clara_training_backend",
        "port": SERVICE_PORT
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=SERVICE_PORT, log_level="info")
```

#### Create `backend/training/__init__.py`

```python
# backend/training/__init__.py
"""Training Backend Package"""

from .app import app
from .manager import TrainingJobManager
from .models import TrainingJob, JobStatus, TrainerType

__version__ = "1.0.0"
__all__ = [
    "app",
    "TrainingJobManager",
    "TrainingJob",
    "JobStatus",
    "TrainerType"
]
```

### Step 1.3: Test Training Backend

```bash
# Start with new structure
python -m backend.training.app

# Test health endpoint
curl http://localhost:45680/health

# If successful: ✅ Training Backend refactored
```

### Step 1.4: Repeat for Dataset Backend

Similar structure for `backend/datasets/`:
- `models.py` - Dataset, DatasetSearchRequest, etc.
- `manager.py` - DatasetManager class
- `quality/pipeline.py` - Quality scoring
- `export/jsonl_exporter.py`, `parquet_exporter.py`, etc.
- `api/routes.py` - API endpoints
- `app.py` - FastAPI app

---

## 🔐 Phase 2: Shared Modules (2-3 hours)

### Step 2.1: Create Shared Auth Module

```bash
mkdir -p shared/auth
```

#### Move `shared/jwt_middleware.py` → `shared/auth/middleware.py`

**Status:** ✅ **COMPLETED**

The file has been moved. Original migration command was:
```bash
# Copy content (COMPLETED)
cp shared/jwt_middleware.py shared/auth/middleware.py
```

#### Extract decorators to `shared/auth/decorators.py`

```python
# shared/auth/decorators.py
"""Auth Decorators"""

from functools import wraps
from fastapi import HTTPException, Depends

from .middleware import jwt_middleware


def require_roles(roles: list):
    """Decorator for role-based access"""
    return jwt_middleware.require_roles(roles)


def optional_auth():
    """Decorator for optional authentication"""
    return jwt_middleware.optional_auth()
```

#### Extract models to `shared/auth/models.py`

```python
# shared/auth/models.py
"""Auth Models"""

from pydantic import BaseModel
from typing import Optional


class SecurityConfig(BaseModel):
    """Security Configuration"""
    mode: str  # production, development, debug, testing
    keycloak_url: Optional[str] = None
    realm: str = "clara"
    client_id: str = "clara-client"
    # ... rest from jwt_middleware.py
```

#### Create `shared/auth/__init__.py`

```python
# shared/auth/__init__.py
"""Auth Package"""

from .middleware import JWTMiddleware, jwt_middleware, get_current_user_email
from .decorators import require_roles, optional_auth
from .models import SecurityConfig

__all__ = [
    "JWTMiddleware",
    "jwt_middleware",
    "get_current_user_email",
    "require_roles",
    "optional_auth",
    "SecurityConfig"
]
```

### Step 2.2: Create Shared Database Module

```bash
mkdir -p shared/database/adapters
```

#### Move `shared/uds3_dataset_search.py` → `shared/database/dataset_search.py`

**Status:** ✅ **COMPLETED**

The file has been moved. Original migration command was:
```bash
# Copy content (COMPLETED)
cp shared/uds3_dataset_search.py shared/database/dataset_search.py
```

#### Create `shared/database/__init__.py`

```python
# shared/database/__init__.py
"""Database Package"""

from .dataset_search import DatasetSearchAPI, DatasetSearchQuery, DatasetDocument

__all__ = [
    "DatasetSearchAPI",
    "DatasetSearchQuery",
    "DatasetDocument"
]
```

### Step 2.3: Test Imports

```python
# Test new imports
from shared.auth.middleware import jwt_middleware
from shared.database.dataset_search import DatasetSearchAPI

print("✅ New imports work!")
```

---

## 🧪 Phase 3: Tests (1-2 hours)

### Step 3.1: Create Test Structure

```bash
mkdir -p tests/{unit,integration,e2e}/{backend,shared,frontend}
```

### Step 3.2: Move Existing Tests

```bash
# Integration tests
mv tests/test_training_backend.py tests/integration/backend/
mv tests/test_dataset_backend.py tests/integration/backend/
mv tests/test_security_integration.py tests/integration/

# Create unit tests (new)
# tests/unit/backend/test_training_manager.py
# tests/unit/shared/test_auth_middleware.py
```

### Step 3.3: Update conftest.py

```python
# tests/conftest.py
"""Global Test Fixtures"""

import pytest
import os

# Set test environment
os.environ["CLARA_SECURITY_MODE"] = "testing"
os.environ["CLARA_ENV"] = "testing"


@pytest.fixture(scope="session")
def test_config():
    """Test configuration"""
    return {
        "env": "testing",
        "security_mode": "testing"
    }
```

---

## ⚙️ Phase 4: Config Management (1-2 hours)

### Step 4.1: Create Config Structure

```bash
mkdir -p config
```

### Step 4.2: Create Base Config

```python
# config/base.py
"""Base Configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class BaseConfig(BaseSettings):
    """Base Configuration for all environments"""
    
    APP_NAME: str = "CLARA"
    DEBUG: bool = False
    
    # Service Ports
    TRAINING_PORT: int = 45680
    DATASET_PORT: int = 45681
    
    # Security
    SECURITY_MODE: str = "development"
    
    # Database
    UDS3_POSTGRES_HOST: str = "192.168.178.94"
    UDS3_POSTGRES_PORT: int = 5432
    
    class Config:
        env_file = ".env"
        env_prefix = "CLARA_"
```

### Step 4.3: Create Environment Configs

```python
# config/development.py
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    SECURITY_MODE: str = "development"
```

```python
# config/production.py
from .base import BaseConfig

class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    SECURITY_MODE: str = "production"
```

### Step 4.4: Create Config Factory

```python
# config/__init__.py
"""Config Factory"""

import os
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .testing import TestingConfig


def get_config() -> BaseConfig:
    """Get configuration based on environment"""
    env = os.environ.get("CLARA_ENV", "development")
    
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig
    }
    
    config_class = configs.get(env, DevelopmentConfig)
    return config_class()


# Global config instance
config = get_config()

__all__ = ["config", "get_config"]
```

---

## 🔄 Phase 5: Update Imports (2-3 hours)

### Step 5.1: Find All Import Statements

```bash
# Search for old imports
grep -r "from shared.jwt_middleware" backend/ shared/ tests/
grep -r "from shared.uds3_dataset_search" backend/ shared/ tests/
grep -r "from scripts.clara_training_backend" tests/
```

### Step 5.2: Update Import Mappings

**Old → New Mappings:**

```python
# Auth
from shared.jwt_middleware import jwt_middleware
→ from shared.auth.middleware import jwt_middleware

from shared.jwt_middleware import get_current_user_email
→ from shared.auth.middleware import get_current_user_email

# Database
from shared.uds3_dataset_search import DatasetSearchAPI
→ from shared.database.dataset_search import DatasetSearchAPI

# Backend Services
from scripts.clara_training_backend import TrainingJobManager
→ from backend.training.manager import TrainingJobManager

from scripts.clara_dataset_backend import DatasetManager
→ from backend.datasets.manager import DatasetManager
```

### Step 5.3: Automated Import Update Script

```python
# scripts/update_imports.py
"""Update all imports to new structure"""

import re
from pathlib import Path

IMPORT_MAPPINGS = {
    "from shared.jwt_middleware": "from shared.auth.middleware",
    "from shared.uds3_dataset_search": "from shared.database.dataset_search",
    "from scripts.clara_training_backend": "from backend.training",
    "from scripts.clara_dataset_backend": "from backend.datasets",
}

def update_imports_in_file(filepath: Path):
    """Update imports in a single file"""
    content = filepath.read_text(encoding="utf-8")
    
    for old, new in IMPORT_MAPPINGS.items():
        content = content.replace(old, new)
    
    filepath.write_text(content, encoding="utf-8")
    print(f"✅ Updated: {filepath}")


def main():
    """Update all Python files"""
    for pattern in ["backend/**/*.py", "shared/**/*.py", "tests/**/*.py"]:
        for filepath in Path(".").glob(pattern):
            if filepath.name != "update_imports.py":
                update_imports_in_file(filepath)


if __name__ == "__main__":
    main()
```

Run:
```bash
python scripts/update_imports.py
```

---

## ✅ Phase 6: Validation (1 hour)

### Step 6.1: Syntax Check

```bash
# Check Python syntax
python -m py_compile backend/**/*.py
python -m py_compile shared/**/*.py
python -m py_compile tests/**/*.py
```

### Step 6.2: Import Check

```bash
# Try importing all modules
python -c "from backend.training import app; print('✅ Training Backend OK')"
python -c "from backend.datasets import app; print('✅ Dataset Backend OK')"
python -c "from shared.auth.middleware import jwt_middleware; print('✅ Auth OK')"
python -c "from shared.database.dataset_search import DatasetSearchAPI; print('✅ Database OK')"
```

### Step 6.3: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Compare with baseline
diff baseline_tests.txt current_tests.txt
```

### Step 6.4: Start Services

```bash
# Terminal 1: Training Backend
python -m backend.training.app

# Terminal 2: Dataset Backend
python -m backend.datasets.app

# Terminal 3: Test endpoints
curl http://localhost:45680/health
curl http://localhost:45681/health
```

---

## 🧹 Phase 7: Cleanup (30 minutes)

### Step 7.1: Move Old Files to Archive

**Status:** ✅ **COMPLETED** - Old files moved to `archive/legacy_backends/`

Original cleanup plan (files now in archive/legacy_backends/):
```bash
mkdir -p archive/pre-refactor
mv scripts/clara_training_backend.py archive/pre-refactor/  # → archive/legacy_backends/
mv scripts/clara_dataset_backend.py archive/pre-refactor/  # → archive/legacy_backends/
# Note: jwt_middleware.py and uds3_dataset_search.py moved to archive/legacy_backends/
```
mv shared/uds3_dataset_search.py archive/pre-refactor/
```

### Step 7.2: Update .gitignore

```bash
# Add to .gitignore
echo "archive/pre-refactor/" >> .gitignore
echo "baseline_tests.txt" >> .gitignore
```

---

## 📋 Phase 8: Git Commit

### Step 8.1: Review Changes

```bash
git status
git diff
```

### Step 8.2: Commit

```bash
git add .
git commit -m "refactor: Reorganize codebase to Clean Architecture

- Separate backend services (training, datasets)
- Restructure shared modules (auth, database, models, utils)
- Implement proper test structure (unit, integration, e2e)
- Add environment-based config management
- Update all imports and documentation
- Add proper __init__.py for all packages

BREAKING CHANGE: Import paths have changed
- shared.jwt_middleware → shared.auth.middleware
- shared.uds3_dataset_search → shared.database.dataset_search
- scripts.clara_training_backend → backend.training
- scripts.clara_dataset_backend → backend.datasets

Tested:
- ✅ All services start successfully
- ✅ All API endpoints working
- ✅ All tests passing (X/X tests)
- ✅ Health checks green
"

git push origin main
```

---

## 🔙 Rollback Strategy

If something goes wrong:

```bash
# Option 1: Revert commit
git revert HEAD

# Option 2: Reset to backup
git reset --hard backup-before-refactor

# Option 3: Cherry-pick good changes
git cherry-pick <commit-hash>
```

---

## 📚 Post-Migration Tasks

### Update Documentation

- [ ] Update README.md with new structure
- [ ] Update API docs with new import paths
- [ ] Create architecture diagrams
- [ ] Update quick start guides

### Deployment Scripts

- [ ] Update `start_training_backend.ps1` to use `backend.training.app`
- [ ] Update `start_dataset_backend.ps1` to use `backend.datasets.app`
- [ ] Move to `admin/deployment/`

### CI/CD

- [ ] Update GitHub Actions workflows
- [ ] Update Docker files
- [ ] Update deployment configs

---

## 🎓 Lessons Learned

### Best Practices Applied

✅ Single Responsibility Principle - Each module has one job  
✅ Open/Closed Principle - Extensible via base classes  
✅ Dependency Inversion - Depend on abstractions not concretions  
✅ Package by Feature - Related code grouped together  
✅ Proper Test Structure - Unit/Integration/E2E separation  

### Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Files in scripts/ | 102 | ~10 | -90% |
| Monolithic files | 2 (900+ lines) | 0 | -100% |
| Package depth | 0 | 3-4 levels | +∞ |
| Test organization | Flat | 3-level | ✅ |
| Shared modules | 2 | 15+ | +750% |

---

## 📞 Support

If you encounter issues:

1. Check baseline tests: `cat baseline_tests.txt`
2. Check syntax: `python -m py_compile <file>`
3. Check imports: Try importing modules manually
4. Rollback if needed: `git reset --hard backup-before-refactor`

---

**Version:** 1.0  
**Last Updated:** 2024-10-24  
**Status:** ✅ READY FOR USE
