# Clara AI System v2.0 - Clean Architecture

AI-System mit kontinuierlichem Lernen, Multi-GPU-Support und Clean Architecture

## 📋 Übersicht

**Zweck:** Maschinelles Lernen, Training und Inferenz mit Microservices-Architektur

**Technologie-Stack:**
- **Backend:** FastAPI, PyTorch, Transformers, QLoRA
- **Architecture:** Clean Architecture, Microservices
- **Infrastructure:** Multi-GPU, WandB, PostgreSQL, Neo4j, ChromaDB
- **Configuration:** Pydantic Settings, Environment-based Config

## 🏗️ Architektur (v2.0)

### Microservices
- **Training Backend** (Port 45680): LoRA/QLoRA Training Management
- **Dataset Backend** (Port 45681): Dataset Creation & Export
- **Main Application**: User Interface & Coordination

### Projekt-Struktur
```
Clara/
├── backend/
│   ├── training/          # Training Microservice
│   └── datasets/          # Dataset Microservice
├── shared/
│   ├── auth/             # Authentication & Authorization
│   └── database/         # Database Utilities
├── config/               # Centralized Configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/                 # Architecture Documentation
```

## ✨ Hauptfunktionen

- **Clean Architecture:** Microservices mit klarer Trennung
- **Kontinuierliches Lernen:** Automated Training Pipelines
- **Multi-GPU Training:** Distributed Training Support
- **QLoRA Fine-Tuning:** Memory-efficient Training
- **REST APIs:** FastAPI-basierte Microservices
- **Monitoring & Metriken:** WandB Integration
- **Database Integration:** PostgreSQL, Neo4j, ChromaDB Support

## 🚀 Schnellstart

### Prerequisites
```bash
# Python 3.13+ required
pip install -r requirements.txt
```

### Services starten
```bash
# Training Backend (Port 45680)
python -m backend.training.app

# Dataset Backend (Port 45681) 
python -m backend.datasets.app

# Main Application (Optional)
python main.py
```

### Environment Configuration
```bash
# Development Mode (JWT enabled)
$env:CLARA_ENVIRONMENT="development"

# Testing Mode (JWT disabled)
$env:CLARA_ENVIRONMENT="testing"

# Production Mode (JWT + mTLS)
$env:CLARA_ENVIRONMENT="production"
```

## 📚 Dokumentation

Weitere Dokumentation finden Sie in:
- [ROADMAP.md](ROADMAP.md) - Geplante Features und Entwicklungsplan
- [DEVELOPMENT.md](DEVELOPMENT.md) - Entwickler-Dokumentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Beitragsrichtlinien

## 🔗 Verwandte Repositories

Teil des [VCC-Projekts](https://github.com/makr-code/VCC)

## 📄 Lizenz

Private Repository - Alle Rechte vorbehalten

## 👤 Autor

**makr-code** - [GitHub](https://github.com/makr-code)

---

*Letzte Aktualisierung: 16.10.2025*
