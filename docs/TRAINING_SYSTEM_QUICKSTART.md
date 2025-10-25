# CLARA Self-Learning LoRa System - Quick Start Guide

**Status:** 🚧 In Development  
**Version:** 1.0.0  
**Datum:** 24. Oktober 2025  
**Security:** 🔐 Environment-Variable Controlled (4 Modes)

---

## 📋 Übersicht

Dieses System implementiert ein selbstlernendes LoRa/QLoRa-Training-System mit:

- ✅ **FastAPI Backend** - Microservices für Training, Dataset-Management, Model Serving
- ✅ **Environment-Variable Security** - 4 Modi (production, development, debug, testing)
- ✅ **JWT + mTLS Support** - Enterprise-Grade Authentication & Authorization
- ✅ **RBAC** - Role-Based Access Control (admin, trainer, analyst, user, auditor)
- ✅ **UDS3 Hybrid Search** - Intelligente Dataset-Auswahl über Vector, Graph & Keyword Search
- ✅ **Continuous Learning** - Automatisches Training basierend auf User-Feedback
- ✅ **WebSocket Live-Updates** - Real-Time Job-Status und Metrics
- ⏳ **vLLM Multi-LoRa** - Skalierbar von Ollama (Dev) zu vLLM (Production)

---

## 🏗️ Architektur

### Microservices

| Service | Port | Status | Beschreibung |
|---------|------|--------|--------------|
| Main Backend | 45678 | ✅ Production | Queries, DSGVO, Review Queue |
| Ingestion Backend | 45679 | ✅ Production | Document Upload, Processing |
| **Training Backend** | **45680** | ✅ **Development** | **LoRa/QLoRa Training Jobs (🔐 JWT Protected)** |
| **Dataset Management** | **45681** | ⏳ Planned | **UDS3 Hybrid Search, Quality Check** |
| **Model Serving** | **45682** | ⏳ Planned | **vLLM Multi-LoRa Inference** |
| Metrics | 9310 | ✅ Production | Prometheus Metrics |

### Security Layer (VCC)

| Service | Port | Status | Beschreibung |
|---------|------|--------|--------------|
| Veritas Edge | 5000 | 🔧 Optional | API Gateway, Routing |
| User Service | 5001 | 🔧 Optional | OIDC, RBAC, JWT Validation |
| PKI Service | 8443 | 🔧 Optional | mTLS Certificates, CA Management |
| Keycloak | 8080 | 🔧 Optional | Identity Provider (only for production/development modes) |

### Datenbanken (UDS3)

- **PostgreSQL** (192.168.178.94:5432) - Metadata, Jobs, Datasets
- **ChromaDB** (192.168.178.94:8000) - Vector Embeddings
- **Neo4j** (192.168.178.94:7687) - Knowledge Graph
- **CouchDB** (192.168.178.94:32931) - JSON Documents

---

## � Security Modes

Das System unterstützt **4 Security Modes** via Environment Variable:

### 1. Debug Mode (Lokale Entwicklung - NO SECURITY ⚠️)

```powershell
# Schnellster Start - kein Keycloak erforderlich
$env:CLARA_SECURITY_MODE = "debug"
python scripts/clara_training_backend.py
```

**Features:**
- ✅ Kein JWT erforderlich
- ✅ Mock User mit allen Rollen (admin, trainer, analyst)
- ✅ Alle Endpoints offen
- ⚠️ **NEVER use in production!**

### 2. Development Mode (JWT Validation)

```powershell
# Für Entwicklung mit Keycloak
$env:CLARA_SECURITY_MODE = "development"
python scripts/clara_training_backend.py
```

**Features:**
- ✅ JWT Validation (Keycloak required)
- ✅ RBAC Enforcement
- ⚠️ No mTLS (HTTP only)

**Requirements:**
- Keycloak Server (Port 8080)
- VCC User Service (Port 5001) - Optional

### 3. Production Mode (Full Security)

```powershell
# Für Production Deployment
$env:CLARA_SECURITY_MODE = "production"
$env:CLARA_JWT_ENABLED = "true"
$env:CLARA_MTLS_ENABLED = "true"
python scripts/clara_training_backend.py
```

**Features:**
- ✅ JWT Validation (RS256)
- ✅ mTLS für Service-to-Service
- ✅ Full RBAC
- ✅ Audit Logging

**Requirements:**
- Keycloak Server (Port 8080)
- VCC User Service (Port 5001)
- PKI Service (Port 8443)

### 4. Testing Mode (Unit Tests)

```powershell
# Für pytest Tests
$env:CLARA_SECURITY_MODE = "testing"
pytest tests/test_security_integration.py
```

**Features:**
- ✅ Mock JWT Validation
- ✅ Fast Execution
- ✅ No external dependencies

---

## 🚀 Quick Start

### Option 1: Interactive Start (Empfohlen)

```powershell
# Interaktiver Start mit Security Mode Auswahl
.\start_training_backend_interactive.ps1
```

**Wähle Security Mode:**
```
1) DEBUG mode (no security, mock user) - Für lokale Entwicklung
2) DEVELOPMENT mode (JWT only, no mTLS) - Für Entwicklung mit Keycloak
3) PRODUCTION mode (JWT + mTLS) - Für Production Deployment
```

### Option 2: Manual Start (Debug Mode)

```powershell
# 1. Aktiviere Virtual Environment
& C:\VCC\Clara\.venv\Scripts\Activate.ps1

# 2. Setze Security Mode
$env:CLARA_SECURITY_MODE = "debug"
$env:CLARA_JWT_ENABLED = "false"
$env:DEBUG_USER_ROLES = "admin,trainer,analyst"

# 3. Starte Backend
python scripts/clara_training_backend.py
```

### Option 3: Manual Start (Development Mode)

```powershell
# Requires Keycloak running on port 8080
$env:CLARA_SECURITY_MODE = "development"
$env:KEYCLOAK_URL = "http://localhost:8080"
$env:KEYCLOAK_REALM = "vcc"
$env:KEYCLOAK_CLIENT_ID = "clara-training-system"

python scripts/clara_training_backend.py
```

**Health Check:**
```powershell
curl http://localhost:45680/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "clara_training_backend",
  "port": 45680,
  "active_jobs": 0,
  "max_concurrent_jobs": 2,
  "timestamp": "2025-10-24T10:00:00"
}
```

---

## 📝 API Verwendung

### Training Job erstellen (🔐 Requires: admin OR trainer role)

**Debug Mode (no auth):**
```powershell
$body = @{
    trainer_type = "qlora"
    config_path = "configs/qlora_config.yaml"
    priority = 3
    tags = @("verwaltungsrecht", "experiment")
} | ConvertTo-Json

curl -X POST http://localhost:45680/api/training/jobs `
  -H "Content-Type: application/json" `
  -d $body
```

**Production/Development Mode (with JWT):**
```powershell
# Get JWT token from Keycloak
$token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."

curl -X POST http://localhost:45680/api/training/jobs `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $token" `
  -d $body
```

**Response:**
```json
{
  "success": true,
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "message": "Training job created: a1b2c3d4...",
  "data": {
    "job_id": "a1b2c3d4...",
    "trainer_type": "qlora",
    "status": "pending",
    "config_path": "configs/qlora_config.yaml",
    "created_at": "2025-10-24T10:05:00",
    "priority": 3,
    "tags": ["verwaltungsrecht", "experiment"]
  }
}
```

### Job-Status abfragen

```powershell
curl http://localhost:45680/api/training/jobs/<job_id>
```

### Alle Jobs auflisten

```powershell
# Alle Jobs
curl http://localhost:45680/api/training/jobs/list

# Nur aktive Jobs
curl "http://localhost:45680/api/training/jobs/list?status=running"
```

### Job abbrechen

```powershell
curl -X DELETE http://localhost:45680/api/training/jobs/<job_id>
```

---

## 🔌 WebSocket Live-Updates

### Python Client

```python
import asyncio
import websockets
import json

async def monitor_training():
    uri = "ws://localhost:45680/ws/training"
    
    async with websockets.connect(uri) as websocket:
        print("🔌 WebSocket verbunden")
        
        # Keep-Alive Loop
        while True:
            try:
                # Warte auf Messages
                message = await websocket.recv()
                data = json.loads(message)
                
                # Job Update verarbeiten
                if data['type'] == 'job_update':
                    print(f"📊 Job {data['job_id'][:8]}... - "
                          f"{data['status']} - "
                          f"{data['progress_percent']:.1f}% - "
                          f"Epoch {data['current_epoch']}/{data['total_epochs']}")
                    
                    if data.get('metrics'):
                        print(f"   Metrics: {data['metrics']}")
            
            except websockets.ConnectionClosed:
                print("🔌 Verbindung geschlossen")
                break

# Starten
asyncio.run(monitor_training())
```

### JavaScript/Browser Client

```javascript
const ws = new WebSocket('ws://localhost:45680/ws/training');

ws.onopen = () => {
    console.log('🔌 WebSocket verbunden');
    
    // Keep-Alive
    setInterval(() => {
        ws.send('ping');
    }, 30000);
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'job_update') {
        console.log(`📊 Job ${data.job_id.substring(0, 8)}...`);
        console.log(`   Status: ${data.status}`);
        console.log(`   Progress: ${data.progress_percent.toFixed(1)}%`);
        console.log(`   Epoch: ${data.current_epoch}/${data.total_epochs}`);
    }
};

ws.onerror = (error) => {
    console.error('❌ WebSocket Error:', error);
};

ws.onclose = () => {
    console.log('🔌 Verbindung geschlossen');
};
```

---

## 📊 Monitoring & Metrics

### Prometheus Metrics

**Endpoint:** `http://localhost:9310/metrics`

**Verfügbare Metriken:**
```
# Training Jobs
training_jobs_total{status="created", type="qlora"}
training_jobs_total{status="started", type="qlora"}
training_jobs_total{status="completed", type="qlora"}
training_jobs_total{status="failed", type="qlora"}

# Active Jobs
active_training_jobs
```

### Grafana Dashboard

TODO: Grafana Dashboard erstellen (siehe docs/SELF_LEARNING_LORA_SYSTEM_ARCHITECTURE.md)

---

## 🔧 Konfiguration

### Environment Variables

```powershell
# Service Config
$env:CLARA_TRAINING_PORT = "45680"
$env:CLARA_MAX_CONCURRENT_JOBS = "2"

# Metrics
$env:CLARA_METRICS_HTTP = "1"
$env:CLARA_METRICS_PORT = "9310"

# UDS3 Connection
$env:UDS3_POSTGRES_HOST = "192.168.178.94"
$env:UDS3_POSTGRES_PORT = "5432"
$env:UDS3_CHROMA_HOST = "192.168.178.94"
$env:UDS3_NEO4J_HOST = "192.168.178.94"
```

### Training Configs

- `configs/lora_config.yaml` - Standard LoRa Training
- `configs/qlora_config.yaml` - Quantized LoRa (4-bit/8-bit)
- `configs/continuous_config.yaml` - Continuous Learning
- `configs/multi_gpu_config.yaml` - Multi-GPU Training

---

## 🧪 Testing

### Unit Tests

```powershell
# Alle Tests
pytest tests/ -v

# Nur Training Backend Tests
pytest tests/test_training_backend.py -v

# Mit Coverage
pytest tests/ --cov=scripts --cov-report=html
```

### Integration Tests

```powershell
# Training Backend + UDS3
pytest tests/test_training_integration.py -v

# End-to-End: Dataset → Training → Serving
pytest tests/test_e2e_workflow.py -v
```

### Manual Testing

```powershell
# 1. Health Check
curl http://localhost:45680/health

# 2. Job erstellen
$job_id = (curl -X POST http://localhost:45680/api/training/jobs `
  -H "Content-Type: application/json" `
  -d '{"trainer_type":"qlora","config_path":"configs/qlora_config.yaml"}' | 
  ConvertFrom-Json).job_id

# 3. Status prüfen
curl http://localhost:45680/api/training/jobs/$job_id

# 4. Jobs auflisten
curl http://localhost:45680/api/training/jobs/list
```

---

## 📚 Dokumentation

### Architektur & Design

- **`docs/SELF_LEARNING_LORA_SYSTEM_ARCHITECTURE.md`** - Vollständige System-Architektur
- `docs/MICROSERVICES_ARCHITECTURE.md` - Microservices-Design (Referenz)
- `docs/WEBSOCKET_INTEGRATION.md` - WebSocket-Pattern (Referenz)

### API Reference

- **Swagger UI:** `http://localhost:45680/docs`
- **ReDoc:** `http://localhost:45680/redoc`

### Implementierungs-Guide

- `docs/TRAINING_BACKEND_IMPLEMENTATION.md` - Backend-Implementierung
- `docs/DATASET_MANAGEMENT_IMPLEMENTATION.md` - Dataset-Service (TODO)
- `docs/MODEL_SERVING_IMPLEMENTATION.md` - vLLM Serving (TODO)

---

## 🛠️ Development Workflow

### 1. Feature entwickeln

```bash
# Neuen Branch erstellen
git checkout -b feature/training-backend-improvements

# Code ändern
# ...

# Tests ausführen
pytest tests/ -v

# Commit
git add .
git commit -m "feat: improve training job management"
```

### 2. Code Review

```bash
# Push to GitHub
git push origin feature/training-backend-improvements

# Pull Request erstellen
# Review durch Team
```

### 3. Deployment

```bash
# Merge to main
git checkout main
git merge feature/training-backend-improvements

# Tag Version
git tag v1.0.1
git push --tags

# Deploy (Docker Compose)
docker-compose up -d training_backend
```

---

## 🐛 Troubleshooting

### Problem: Training Backend startet nicht

**Fehler:** `ModuleNotFoundError: No module named 'scripts.clara_train_lora'`

**Lösung:**
```powershell
# Prüfe PYTHONPATH
$env:PYTHONPATH = "c:\VCC\Clara"

# Oder installiere als Package
pip install -e .
```

### Problem: WebSocket Verbindung schlägt fehl

**Fehler:** `WebSocket connection failed`

**Lösung:**
```powershell
# Prüfe ob Service läuft
curl http://localhost:45680/health

# Prüfe Firewall
Test-NetConnection -ComputerName localhost -Port 45680

# CORS-Header prüfen (Browser Console)
```

### Problem: Job bleibt in Status "queued"

**Mögliche Ursachen:**
1. Maximale concurrent Jobs erreicht (default: 2)
2. GPU nicht verfügbar
3. Worker-Thread Fehler

**Debug:**
```powershell
# Logs prüfen
cat logs/training_backend.log

# Active Jobs prüfen
curl http://localhost:45680/api/training/jobs/list?status=running

# Service neu starten
# Ctrl+C im Terminal, dann neu starten
```

---

## 🎯 Roadmap

### ✅ Phase 1: Foundation (Completed)
- [x] Architektur-Dokument
- [x] Training Backend Service (Basic)
- [x] Job Management System
- [x] WebSocket Integration
- [x] API Documentation

### 🚧 Phase 2: Dataset Integration (In Progress)
- [ ] Dataset Management Service (Port 45681)
- [ ] UDS3 Hybrid Search Integration
- [ ] Quality Checker
- [ ] Dataset Registry
- [ ] Frontend: Dataset Explorer

### ⏳ Phase 3: Continuous Learning (Planned)
- [ ] ContinuousLoRATrainer erweitern
- [ ] Feedback-Pipeline
- [ ] Auto-Training Triggers
- [ ] Quality Gates
- [ ] Frontend: Training Monitor

### ⏳ Phase 4: Model Serving (Planned)
- [ ] vLLM Multi-LoRa Serving
- [ ] Adapter Hot-Swap
- [ ] Router-Integration
- [ ] Load Balancing
- [ ] Frontend: Adapter Manager

### ⏳ Phase 5: Production Ready (Planned)
- [ ] Security (JWT, RBAC)
- [ ] Monitoring (Grafana)
- [ ] Docker Compose
- [ ] CI/CD Pipeline
- [ ] Load Testing

---

## 📞 Support & Kontakt

- **GitHub Issues:** [VCC-Clara Issues](https://github.com/makr-code/VCC-Clara/issues)
- **Dokumentation:** `docs/`
- **Team:** Development Team

---

**Letzte Aktualisierung:** 24. Oktober 2025  
**Version:** 1.0.0  
**Status:** 🚧 In Active Development
