# Clara AI - System Architecture

**Version:** 2.0.0  
**Date:** 2025-11-17  
**Status:** ✅ **PRODUCTION READY**  
**Maintainer:** VCC Team

> **Note:** This is the primary architecture document. For specialized topics, see:
> - **[FRONTEND_ARCHITECTURE.md](./FRONTEND_ARCHITECTURE.md)** - Frontend architecture details
> - **[SECURITY_FRAMEWORK.md](./SECURITY_FRAMEWORK.md)** - Security & authentication
> - **[IMPLEMENTATION_HISTORY.md](./IMPLEMENTATION_HISTORY.md)** - Implementation timeline

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Backend Services](#backend-services)
4. [Frontend Applications](#frontend-applications)
5. [Database Integration](#database-integration)
6. [Security & Authentication](#security--authentication)
7. [Configuration System](#configuration-system)
8. [Deployment Architecture](#deployment-architecture)
9. [Core Processes](#core-processes)

---

## Executive Summary

**CLARA (Cognitive Legal and Administrative Reasoning Assistant)** is an advanced AI system for continuous learning in administrative and legal domains. The system combines modern LoRA/QLoRA training techniques with intelligent REST APIs, microservices architecture, and comprehensive data management.

### Key Features

- ✅ **Continuous Learning:** Automatic model improvement through user feedback
- ✅ **Microservices Architecture:** Training Backend (Port 45680), Dataset Backend (Port 45681)
- ✅ **REST APIs:** Full integration into existing applications
- ✅ **Batch Processing:** Processing of large datasets (millions of documents)
- ✅ **Multi-GPU Support:** Scalable training infrastructure
- ✅ **Frontend Applications:** 3 tkinter GUIs (Admin, Training, Data Preparation)
- ✅ **UDS3 Integration:** Optional polyglot database (PostgreSQL, ChromaDB, Neo4j, CouchDB)
- ✅ **Security Framework:** JWT authentication with 4 security modes

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend Framework** | FastAPI + Uvicorn |
| **Frontend Framework** | tkinter (Python) |
| **Training Framework** | LoRA/QLoRA (Hugging Face) |
| **Database (Primary)** | PostgreSQL |
| **Database (Optional)** | UDS3 (ChromaDB, Neo4j, CouchDB) |
| **Authentication** | JWT (Keycloak OIDC) |
| **Configuration** | Pydantic Settings |
| **API Documentation** | OpenAPI/Swagger |

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Admin        │  │ Training     │  │ Data Prep    │             │
│  │ Frontend     │  │ Frontend     │  │ Frontend     │             │
│  │ (tkinter)    │  │ (tkinter)    │  │ (tkinter)    │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
└─────────┼──────────────────┼──────────────────┼───────────────────┘
          │                  │                  │
          │  HTTP/REST       │  HTTP/REST       │  HTTP/REST
          │  WebSocket       │  (Port 45680)    │  (Port 45681)
          │                  │                  │
┌─────────┼──────────────────┼──────────────────┼───────────────────┐
│         │                  │                  │                    │
│    ┌────▼────────┐    ┌───▼─────────┐   ┌───▼──────────┐         │
│    │             │    │             │   │              │         │
│    │  Training   │◄───┤  Continuous │   │   Dataset    │         │
│    │  Backend    │    │   Learning  │   │   Backend    │         │
│    │  (45680)    │    │   System    │   │   (45681)    │         │
│    │             │    │             │   │              │         │
│    └─────┬───────┘    └─────┬───────┘   └──────┬───────┘         │
│          │                  │                   │                  │
│          │                  │                   │                  │
└──────────┼──────────────────┼───────────────────┼─────────────────┘
           │                  │                   │
           │  UDS3 (Optional) │                   │
           │  ┌───────────────▼──────────┐        │
           │  │                           │        │
           │  │  PostgreSQL  ChromaDB     │◄───────┘
           │  │  Neo4j       CouchDB      │
           │  │                           │
           │  └───────────────────────────┘
           │
           │  Training Data
           ▼
    ┌──────────────┐
    │   Models/    │
    │  Checkpoints │
    └──────────────┘
```

### Component Overview

| Component | Port | Purpose | Status |
|-----------|------|---------|--------|
| **Training Backend** | 45680 | Training job management, WebSocket updates | ✅ Production |
| **Dataset Backend** | 45681 | Dataset management, export, UDS3 search | ✅ Production |
| **Admin Frontend** | - | System administration, monitoring | ✅ Production |
| **Training Frontend** | - | Training job management | ✅ Production |
| **Data Prep Frontend** | - | Dataset preparation | ✅ Production |
| **UDS3 Database** | Various | Optional polyglot database | 🟡 Optional |

---

## Backend Services

### 1. Training Backend (Port 45680)

**File:** `backend/training/app.py`  
**Purpose:** Training job orchestration and management

#### Features

- ✅ **Job Management:** Create, list, cancel, monitor training jobs
- ✅ **WebSocket Live Updates:** Real-time job progress broadcasting (`/ws/jobs`)
- ✅ **Worker Pool:** Background task processing with async workers
- ✅ **Job Queue:** Priority-based job scheduling
- ✅ **Progress Tracking:** Epoch progress, metrics, loss curves
- ✅ **Graceful Degradation:** Works without external dependencies (debug mode)

#### API Endpoints

```
POST   /api/training/jobs              # Create training job
GET    /api/training/jobs              # List all jobs
GET    /api/training/jobs/{job_id}     # Get job details
DELETE /api/training/jobs/{job_id}     # Cancel job
GET    /api/training/jobs/{job_id}/metrics  # Get job metrics
WS     /ws/jobs                         # WebSocket for live updates
GET    /health                          # Health check
GET    /docs                            # OpenAPI/Swagger docs
```

#### Configuration

```python
# Environment variables
CLARA_TRAINING_PORT=45680              # Service port
CLARA_MAX_CONCURRENT_JOBS=2            # Max parallel jobs
CLARA_WORKER_TIMEOUT=3600              # Worker timeout (seconds)
```

---

### 2. Dataset Backend (Port 45681)

**File:** `backend/datasets/app.py`  
**Purpose:** Dataset preparation and management

#### Features

- ✅ **Dataset Management:** Create, delete, export datasets
- ✅ **Multi-Format Export:** JSONL, Parquet, CSV with progress tracking
- ✅ **UDS3 Integration (Optional):** Hybrid search (vector + graph + keyword)
- ✅ **Dataset Statistics:** Quality metrics, distribution analysis
- ✅ **Batch Processing:** Efficient large dataset handling

#### API Endpoints

```
POST   /api/datasets                   # Create dataset
GET    /api/datasets                   # List all datasets
GET    /api/datasets/{id}              # Get dataset details
DELETE /api/datasets/{id}              # Delete dataset
POST   /api/datasets/{id}/export       # Export dataset
GET    /api/datasets/{id}/statistics   # Get statistics
POST   /api/search/datasets            # Search datasets (UDS3)
GET    /health                          # Health check
GET    /docs                            # OpenAPI/Swagger docs
```

#### Configuration

```python
# Environment variables
CLARA_DATASET_PORT=45681               # Service port
CLARA_DATASET_CACHE_DIR=data/cache/    # Cache directory
```

---

### 3. Continuous Learning System

**File:** `backend/continuous_learning/`  
**Purpose:** Automatic model improvement from feedback

#### Components

- **LiveLearningBuffer:** Collects feedback data intelligently
- **ContinuousLoRATrainer:** Executes automatic training cycles
- **Quality Filtering:** Automatically evaluates feedback quality
- **Checkpoint Management:** Automatic model backup

#### Workflow

```
User Interaction → Feedback Collection → Quality Assessment → 
Buffer Aggregation → Automatic Training → Model Update → 
Improved Responses
```

#### Features

- ✅ **Real-time Feedback:** Immediate integration of user corrections
- ✅ **Intelligent Buffering:** Optimal batch sizes for training
- ✅ **Quality Filter:** Automatic feedback quality assessment
- ✅ **Graceful Degradation:** System runs even with trainer errors

---

## Frontend Applications

### Overview

Clara AI features **3 separate tkinter GUIs** following **Clean Architecture** and **OOP Best Practices**.

For detailed frontend documentation, see **[FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md)**.

### 1. Admin Frontend

**File:** `frontend/admin/app.py`  
**Purpose:** System administration and monitoring

**Key Features:**
- Real-Time Metrics Dashboard (CPU, Memory, Disk I/O)
- Enhanced System Logs Viewer (filter, search, export)
- Audit Log Viewer
- Database Management (UDS3 backends)
- System Configuration Browser
- Service Control (Start/Stop/Restart)

### 2. Training Frontend

**File:** `frontend/training/app.py`  
**Purpose:** Training job management

**Key Features:**
- Job creation and cancellation
- Job Metrics Viewer (4 tabs: Loss, Accuracy, Learning Rate, GPU)
- Real-time job updates via WebSocket (🟢 Live indicator)
- Training Config Manager (YAML editor)
- Training Output Files Browser
- Service control

### 3. Data Preparation Frontend

**File:** `frontend/data_preparation/app.py`  
**Purpose:** Dataset creation and management

**Key Features:**
- Dataset creation and deletion
- Dataset Export (JSONL/Parquet/CSV with progress)
- Dataset Statistics Viewer (3 tabs)
- Exported Files Browser
- Drag & Drop file upload (if tkinterdnd2 available)
- Dataset status filtering

### Shared Components

**File:** `frontend/shared/components/base_window.py`

**BaseWindow Abstract Class** provides:
- ✅ Standard Menu Bar (File, View, Tools, Help)
- ✅ Customizable Toolbar
- ✅ Collapsible Sidebar
- ✅ Status Bar with connection indicators
- ✅ VCC Corporate Identity styling

---

## Database Integration

### Primary Database: PostgreSQL

**Connection:** `192.168.178.94:5432`  
**Database:** `postgres`  
**Schema:** `public`

**Purpose:**
- Document storage and retrieval
- Metadata management
- Job and dataset tracking
- Audit logging

**Configuration:**
```python
POSTGRES_CONFIG = {
    'host': '192.168.178.94',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'postgres',
    'schema': 'public'
}
```

### Optional: UDS3 Polyglot Database

**Status:** 🟡 OPTIONAL (System works without it)

For details, see **[UDS3_STATUS.md](./UDS3_STATUS.md)**.

#### UDS3 Components

| Database | Port | Purpose | Status |
|----------|------|---------|--------|
| **PostgreSQL** | 5432 | Relational data, full-text search | ✅ Available |
| **ChromaDB** | 8000 | Vector embeddings, semantic search | 🟡 Optional |
| **Neo4j** | 7687 | Graph relationships, knowledge graph | 🟡 Optional |
| **CouchDB** | 32931 | JSON document storage | 🟡 Optional |

#### Hybrid Search

When UDS3 is available, dataset search uses:
- **Vector Search:** Semantic similarity via ChromaDB embeddings
- **Graph Search:** Relationship-based queries via Neo4j
- **Keyword Search:** PostgreSQL full-text search
- **Hybrid Scoring:** Weighted combination of all three

---

## Security & Authentication

For detailed security documentation, see **[SECURITY_FRAMEWORK.md](./SECURITY_FRAMEWORK.md)**.

### Security Modes

| Mode | JWT | mTLS | Use Case |
|------|-----|------|----------|
| **production** | ✅ Required | ✅ Required | Production deployment |
| **development** | ✅ Required | ❌ Optional | Development with auth |
| **debug** | ❌ Mock user | ❌ Disabled | Local development |
| **testing** | ✅ Mock JWT | ❌ Disabled | Automated tests |

### JWT Authentication

**File:** `shared/auth/middleware.py`

**Features:**
- ✅ Keycloak OIDC Integration (RS256)
- ✅ Role-Based Access Control (RBAC)
- ✅ Token validation and refresh
- ✅ Mock user for offline development

**RBAC Helpers:**
```python
@require_roles(['admin'])           # Require admin role
@optional_auth()                    # Auth optional
has_role(token, 'trainer')         # Check role
```

### Configuration

```bash
# Security mode
export CLARA_SECURITY_MODE=production  # or development, debug, testing

# Keycloak settings
export KEYCLOAK_URL=https://keycloak.example.com
export KEYCLOAK_REALM=vcc
export KEYCLOAK_CLIENT_ID=clara-training-system

# Override auto-detection
export CLARA_JWT_ENABLED=true
export CLARA_MTLS_ENABLED=true
```

---

## Configuration System

For complete configuration reference, see **[CONFIGURATION_REFERENCE.md](./CONFIGURATION_REFERENCE.md)**.

### Centralized Configuration

**Files:**
- `config/base.py` - Base configuration with defaults
- `config/development.py` - Development overrides
- `config/production.py` - Production overrides
- `config/testing.py` - Testing overrides
- `config/__init__.py` - Configuration loader

### Key Configuration Options

```python
from config import config

# Application settings
config.app_name                    # "Clara Training System"
config.environment                 # development/production/testing
config.debug                       # Debug mode

# Backend service ports
config.training_port               # 45680 (default)
config.dataset_port                # 45681 (default)

# Security settings
config.security_mode               # production/development/debug/testing
config.jwt_enabled                 # Auto-determined from security_mode
config.mtls_enabled                # Auto-determined from security_mode

# Worker configuration
config.max_concurrent_jobs         # 2 (default)
config.worker_timeout              # 3600 seconds (default)
```

### Environment Variables

All configuration can be overridden via `CLARA_*` environment variables:

```bash
export CLARA_ENVIRONMENT=production
export CLARA_TRAINING_PORT=8080
export CLARA_DATASET_PORT=8081
export CLARA_SECURITY_MODE=production
export CLARA_MAX_CONCURRENT_JOBS=4
```

---

## Deployment Architecture

### Development Deployment

```bash
# Start services locally
python -m backend.training.app      # Port 45680
python -m backend.datasets.app      # Port 45681

# Start frontends
python frontend/admin/app.py
python frontend/training/app.py
python frontend/data_preparation/app.py
```

### Production Deployment

#### Option 1: Direct Deployment

```bash
# Set production environment
export CLARA_ENVIRONMENT=production
export CLARA_SECURITY_MODE=production

# Start services with Uvicorn
uvicorn backend.training.app:app --host 0.0.0.0 --port 45680 --workers 4
uvicorn backend.datasets.app:app --host 0.0.0.0 --port 45681 --workers 4
```

#### Option 2: Docker Deployment (Planned)

```yaml
# docker-compose.yml
version: '3.8'
services:
  training-backend:
    build: .
    ports:
      - "45680:45680"
    environment:
      - CLARA_ENVIRONMENT=production
      - CLARA_TRAINING_PORT=45680
  
  dataset-backend:
    build: .
    ports:
      - "45681:45681"
    environment:
      - CLARA_ENVIRONMENT=production
      - CLARA_DATASET_PORT=45681
```

#### Option 3: Kubernetes Deployment (Planned)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clara-training-backend
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: training
        image: clara-training:latest
        ports:
        - containerPort: 45680
```

### System Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- GPU: None (CPU training works)
- Storage: 20 GB

**Recommended:**
- CPU: 8+ cores
- RAM: 32 GB
- GPU: NVIDIA with 16+ GB VRAM
- Storage: 100+ GB SSD

---

## Core Processes

### 1. Continuous Learning Cycle

```
User Interaction → Feedback Collection → Quality Assessment → 
Buffer Aggregation → Automatic Training → Model Update → 
Improved Responses
```

**Features:**
- Real-time feedback integration
- Intelligent buffering (optimal batch sizes)
- Quality filtering (automatic assessment)
- Graceful degradation (runs even with trainer errors)

### 2. Training Job Workflow

```
Job Creation → Validation → Queue → Worker Assignment → 
Training Execution → Progress Updates (WebSocket) → 
Checkpoint Saving → Completion
```

**Optimizations:**
- Background task processing
- Automatic resume on interruption
- Multi-GPU support
- Progress streaming via WebSocket

### 3. Dataset Preparation Workflow

```
Data Source → Format Detection → Parallel Extraction → 
Duplicate Detection → Quality Assessment → Training Data Generation → 
Export (JSONL/Parquet/CSV)
```

**Optimizations:**
- Multi-core processing
- Memory-efficient streaming
- Format support: PDF, Word, Markdown, JSON, CSV, Archives

### 4. UDS3 Hybrid Search (Optional)

```
Query → Vector Embedding → Parallel Search:
  ├── Vector Search (ChromaDB)
  ├── Graph Search (Neo4j)
  └── Keyword Search (PostgreSQL)
→ Score Aggregation → Ranking → Results
```

**Benefits:**
- Semantic similarity (vector)
- Relationship discovery (graph)
- Exact matches (keyword)
- Hybrid scoring for best results

---

## Directory Structure

```
clara-ai/
├── backend/                        # Backend Services
│   ├── training/                   # Training Backend (Port 45680)
│   │   ├── app.py                  # FastAPI application
│   │   ├── manager.py              # Job management
│   │   └── api/                    # API routes
│   ├── datasets/                   # Dataset Backend (Port 45681)
│   │   ├── app.py                  # FastAPI application
│   │   ├── manager.py              # Dataset management
│   │   └── api/                    # API routes
│   └── continuous_learning/        # Continuous learning system
├── frontend/                       # Frontend Applications
│   ├── shared/                     # Shared components
│   │   ├── components/             # Base classes
│   │   ├── api/                    # API clients
│   │   └── utils/                  # Utilities
│   ├── admin/                      # Admin Frontend
│   ├── training/                   # Training Frontend
│   └── data_preparation/           # Data Prep Frontend
├── shared/                         # Shared Modules
│   ├── auth/                       # Authentication
│   │   └── middleware.py           # JWT middleware
│   └── database/                   # Database modules
│       └── dataset_search.py       # UDS3 integration
├── config/                         # Configuration
│   ├── base.py                     # Base config
│   ├── development.py              # Dev config
│   ├── production.py               # Prod config
│   └── testing.py                  # Test config
├── models/                         # Trained models
├── data/                           # Data directory
└── docs/                           # Documentation
    └── archive/                    # Historical docs
```

---

## Related Documentation

### Primary Documentation
- **[FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md)** - Complete frontend guide
- **[SECURITY_FRAMEWORK.md](./SECURITY_FRAMEWORK.md)** - Security details
- **[CONFIGURATION_REFERENCE.md](./CONFIGURATION_REFERENCE.md)** - All config options
- **[UDS3_STATUS.md](./UDS3_STATUS.md)** - UDS3 integration status

### Implementation
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Current status
- **[IMPLEMENTATION_HISTORY.md](./IMPLEMENTATION_HISTORY.md)** - Timeline

### Historical (Archived)
- **[archive/implementation/](./archive/implementation/)** - Phase reports
- **[SELF_LEARNING_LORA_SYSTEM_ARCHITECTURE.md](./SELF_LEARNING_LORA_SYSTEM_ARCHITECTURE.md)** - Original architecture plan (now implemented)
- **[ARCHITECTURE_REFACTORING_PLAN.md](./ARCHITECTURE_REFACTORING_PLAN.md)** - Refactoring plan (now complete)

---

**Last Updated:** 2025-11-17  
**Maintainer:** VCC Team  
**Version:** 2.0.0 (Production)
