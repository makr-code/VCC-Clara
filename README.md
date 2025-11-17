# Clara AI System v2.0 - Continuous Learning & Clean Architecture

[![Documentation](https://img.shields.io/badge/docs-comprehensive-blue)](docs/)
[![Python](https://img.shields.io/badge/python-3.13%2B-blue)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-microservices-green)](docs/ARCHITECTURE.md)
[![License](https://img.shields.io/badge/license-private-red)](LICENSE)

**Production-ready AI system with continuous learning, microservices architecture, and comprehensive documentation.**

## 📋 Overview

Clara is an AI training and inference platform built with Clean Architecture principles, featuring:

- **Automated Continuous Learning:** Self-improving AI models with automated training pipelines
- **Microservices Architecture:** Independent, scalable backend services
- **Multi-Database Support:** PostgreSQL + optional UDS3 (ChromaDB, Neo4j, CouchDB)
- **Production-Ready:** Complete deployment guides, monitoring, and troubleshooting support
- **QLoRA Fine-Tuning:** Memory-efficient training with LoRA adapters
- **REST APIs:** FastAPI-based services with complete API documentation

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Backend** | FastAPI, PyTorch, Transformers | Python 3.13+ |
| **Architecture** | Microservices, Clean Architecture | - |
| **Databases** | PostgreSQL (required), UDS3 (optional) | PostgreSQL 13+ |
| **Configuration** | Pydantic Settings | v2+ |
| **Testing** | pytest | 8.4.2 |
| **Monitoring** | WandB, Prometheus | - |

## 🏗️ Architecture

Clara uses a **microservices architecture** with three independent backend services:

### Backend Services

| Service | Port | Purpose | Documentation |
|---------|------|---------|---------------|
| **Training Backend** | 45680 | LoRA/QLoRA training jobs | [API Reference](docs/API_REFERENCE.md#training-backend-api) |
| **Dataset Backend** | 45681 | Dataset creation & export | [API Reference](docs/API_REFERENCE.md#dataset-backend-api) |
| **Continuous Learning** | - | Automated training pipeline | [Architecture](docs/ARCHITECTURE.md#continuous-learning-system) |

### Frontend Applications

Three tkinter-based GUI applications:
- **Admin Frontend:** System management, service control
- **Training Frontend:** Training job management, monitoring
- **Data Preparation Frontend:** Dataset creation, export

📖 **[Complete Architecture Guide →](docs/ARCHITECTURE.md)**

### Project Structure

```
VCC-Clara/
├── backend/              # Backend microservices
│   ├── training/         # Training service (Port 45680)
│   ├── datasets/         # Dataset service (Port 45681)
│   └── continuous_learning/  # Automated training
├── frontend/             # GUI applications (3 apps)
├── shared/               # Shared modules
│   ├── auth/             # JWT authentication, RBAC
│   └── database/         # Database utilities
├── config/               # Centralized configuration
├── tests/                # Test suite (unit, integration, e2e)
├── docs/                 # Comprehensive documentation
└── scripts/              # Utility scripts
```

## ✨ Key Features

### Continuous Learning System
- **Automated Training Pipeline:** Monitors review queue, triggers training automatically
- **Self-Improvement:** System learns from corrected predictions
- **LoRA/QLoRA Support:** Memory-efficient fine-tuning with adapter weights
- **Multi-GPU Training:** Distributed training across multiple GPUs

### Microservices Architecture
- **Independent Services:** Training and Dataset backends run independently
- **REST APIs:** Complete FastAPI-based APIs with OpenAPI/Swagger documentation
- **Scalable:** Each service can be scaled independently
- **Production-Ready:** Systemd services, Docker deployment, Nginx reverse proxy

### Database Integration
- **PostgreSQL:** Primary relational database (required)
- **UDS3 Framework:** Optional polyglot database support
  - **ChromaDB:** Vector similarity search
  - **Neo4j:** Graph relationships and knowledge graphs
  - **CouchDB:** JSON document storage
- **Graceful Degradation:** System works without UDS3 (basic features only)

### Security & Authentication
- **JWT Tokens:** Secure API authentication
- **RBAC:** Role-based access control (4 roles: admin, trainer, analyst, viewer)
- **4 Security Modes:** development, jwt_optional, jwt_required, production
- **mTLS Support:** Mutual TLS for production deployments

### Frontend Applications (23 Features)
- **Dataset Export:** JSONL, Parquet, CSV with progress tracking
- **Job Management:** Create, monitor, cancel training jobs
- **Service Control:** Start/stop/restart backend services
- **Real-Time Updates:** WebSocket-based job status updates
- **Advanced UI:** Keyboard shortcuts, sortable columns, drag & drop

📖 **[Frontend Guide →](docs/FRONTEND_GUIDE.md)** | **[Feature List →](docs/FRONTEND_FEATURES_QUICK_REFERENCE.md)**

## 🚀 Quick Start

### Prerequisites

**System Requirements:**
- **Python:** 3.13+ (required)
- **PostgreSQL:** 13+ (required)
- **Memory:** 8 GB RAM minimum, 16 GB recommended
- **GPU:** Optional (CUDA 11.8+ for training)

**Installation:**

```bash
# 1. Clone repository
git clone https://github.com/makr-code/VCC-Clara
cd VCC-Clara

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment (copy and edit)
cp .env.example .env
# Edit .env with your settings
```

📖 **[Complete Installation Guide →](docs/DEPLOYMENT_GUIDE.md#development-setup)**

### Start Backend Services

**Option 1: Quick Start (Development)**

```bash
# Training Backend (Terminal 1)
python -m backend.training.app

# Dataset Backend (Terminal 2)
python -m backend.datasets.app
```

**Option 2: PowerShell Scripts (Windows)**

```powershell
# Start both backends
.\scripts\start_backends.ps1

# Stop both backends
.\scripts\stop_backends.ps1
```

**Option 3: Docker Deployment**

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

📖 **[Deployment Guide →](docs/DEPLOYMENT_GUIDE.md)** | **[Docker Guide →](docs/DEPLOYMENT_GUIDE.md#docker-deployment)**

### Verify Installation

```bash
# Check Training Backend
curl http://localhost:45680/health

# Check Dataset Backend
curl http://localhost:45681/health

# Run health check script
python scripts/health_check.py
```

### Configuration

Clara supports multiple deployment modes:

```bash
# Development (JWT optional, debug logging)
export CLARA_SECURITY_MODE=development

# Production (JWT + RBAC required)
export CLARA_SECURITY_MODE=production

# Testing (Mock JWT for automated tests)
export CLARA_SECURITY_MODE=testing
```

📖 **[Configuration Reference →](docs/CONFIGURATION_REFERENCE.md)**

## 📚 Documentation

### Core Documentation

| Document | Description | Audience |
|----------|-------------|----------|
| **[Architecture Guide](docs/ARCHITECTURE.md)** | System architecture, components, workflows | All |
| **[API Reference](docs/API_REFERENCE.md)** | Complete REST API documentation (8 endpoints) | Developers |
| **[Configuration Reference](docs/CONFIGURATION_REFERENCE.md)** | All configuration options and environment variables | Ops, Developers |
| **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** | Development, production, Docker deployment | Ops, DevOps |
| **[Testing Guide](docs/TESTING_GUIDE.md)** | Running tests, writing tests, fixtures, coverage | QA, Developers |
| **[Troubleshooting Guide](docs/TROUBLESHOOTING_GUIDE.md)** | 20+ common issues and solutions | Support, Ops |
| **[Frontend Guide](docs/FRONTEND_GUIDE.md)** | GUI applications and 23 features | End Users |

### Additional Documentation

| Document | Description |
|----------|-------------|
| **[Implementation History](docs/IMPLEMENTATION_HISTORY.md)** | Development timeline and milestones |
| **[UDS3 Status](docs/UDS3_STATUS.md)** | Optional UDS3 integration guide |
| **[Frontend Features](docs/FRONTEND_FEATURES_QUICK_REFERENCE.md)** | Quick reference for all 23 features |
| **[Security Framework](docs/SECURITY_FRAMEWORK.md)** | JWT, RBAC, authentication details |

📖 **[Complete Documentation Index →](docs/README.md)**

### Quick Links

- **Getting Started:** [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) → [Configuration](docs/CONFIGURATION_REFERENCE.md) → [API Reference](docs/API_REFERENCE.md)
- **Troubleshooting:** [Common Issues](docs/TROUBLESHOOTING_GUIDE.md) → [Health Checks](docs/TROUBLESHOOTING_GUIDE.md#logging-and-diagnostics)
- **Development:** [Testing Guide](docs/TESTING_GUIDE.md) → [Architecture](docs/ARCHITECTURE.md) → [Contributing](CONTRIBUTING.md)

## 🧪 Testing

Clara includes comprehensive test coverage:

```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run with coverage report
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/config/test_config.py -v
```

**Test Statistics:**
- **Total Tests:** 33+ (23 unit, 10+ integration)
- **Coverage:** ~60% (target: >80%)
- **Framework:** pytest 8.4.2
- **Test Types:** Unit, Integration, E2E

📖 **[Testing Guide →](docs/TESTING_GUIDE.md)**

## 🛠️ Development

### Project Status

| Component | Status | Version | Documentation |
|-----------|--------|---------|---------------|
| **Training Backend** | ✅ Production | 2.0 | [API](docs/API_REFERENCE.md#training-backend-api) |
| **Dataset Backend** | ✅ Production | 2.0 | [API](docs/API_REFERENCE.md#dataset-backend-api) |
| **Frontend (3 Apps)** | ✅ Production | 2.0 | [Guide](docs/FRONTEND_GUIDE.md) |
| **Continuous Learning** | ✅ Implemented | 2.0 | [Architecture](docs/ARCHITECTURE.md) |
| **Documentation** | ✅ Complete | 2.0 | [Index](docs/README.md) |

### Continuous Learning Pipeline

Clara implements an automated continuous learning system:

1. **Review Queue Monitoring:** Continuously monitors for corrected predictions
2. **Automated Triggering:** Starts training when threshold reached (configurable)
3. **LoRA Fine-Tuning:** Memory-efficient adapter training
4. **Model Deployment:** Automatic model version management
5. **Feedback Loop:** System improves from corrections

📖 **[Continuous Learning Details →](docs/ARCHITECTURE.md#continuous-learning-system)**

## 🔗 Related Projects

Clara is part of the [VCC Project ecosystem](https://github.com/makr-code/VCC).

### Related Repositories

- **UDS3:** Polyglot database framework (optional dependency)
- **VCC:** Parent project and coordination repository

## 🤝 Contributing

We welcome contributions! Please see:

- **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute
- **[Code of Conduct](CODE_OF_CONDUCT.md)** - Community standards
- **[Development Guide](DEVELOPMENT.md)** - Development setup and practices

### Reporting Issues

Found a bug? Have a suggestion?

1. Check existing issues first
2. Use issue templates (Bug Report, Feature Request)
3. Provide as much detail as possible
4. Include logs and error messages

## 📊 Monitoring & Observability

Clara includes built-in monitoring:

- **Health Checks:** `/health` endpoints on all services
- **Prometheus Metrics:** Available on port 9310
- **WandB Integration:** Training metrics and experiment tracking
- **Logging:** Structured logging with configurable levels

📖 **[Monitoring Guide →](docs/DEPLOYMENT_GUIDE.md#health-checks--monitoring)**

## 🔒 Security

Clara implements multiple security layers:

- **JWT Authentication:** Token-based API authentication
- **RBAC:** 4 roles with granular permissions
- **mTLS Support:** Mutual TLS for production
- **Environment Isolation:** Separate dev/test/production configs
- **Security Modes:** 4 configurable security levels

📖 **[Security Guide →](docs/SECURITY_FRAMEWORK.md)**

## 📄 License

**Private Repository** - All rights reserved

## 👤 Author

**makr-code** - [GitHub](https://github.com/makr-code)

## 📞 Support

Need help?

1. **Documentation:** Check [docs/](docs/) directory
2. **Troubleshooting:** See [TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md)
3. **Issues:** Create an issue on GitHub
4. **Community:** Join discussions

---

**Last Updated:** 2025-11-17  
**Documentation Version:** 2.0  
**System Status:** ✅ Production Ready
