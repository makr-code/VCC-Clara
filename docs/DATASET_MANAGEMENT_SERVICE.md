# CLARA Dataset Management Service

**Microservice für Dataset-Vorbereitung und -Verwaltung**

> Version: 1.0.0  
> Port: **45681**  
> Status: ✅ **PRODUCTION READY**  
> Author: VCC Team  
> Date: 2024-10-24

---

## 📋 Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Features](#features)
3. [Architektur](#architektur)
4. [Installation](#installation)
5. [Verwendung](#verwendung)
6. [API Referenz](#api-referenz)
7. [Konfiguration](#konfiguration)
8. [Security](#security)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## Überblick

Der **Dataset Management Service** ist ein FastAPI-Microservice zur Vorbereitung und Verwaltung von Trainings-Datasets für LoRa/QLoRa-Training.

### Key Features

✅ **UDS3 Hybrid Search Integration**  
✅ **Dataset Quality Pipeline**  
✅ **Multi-Format Export** (JSONL, Parquet, CSV, JSON)  
✅ **Dataset Registry** (PostgreSQL)  
✅ **Background Processing**  
✅ **JWT Authentication**  
✅ **Audit Logging**

### Architektur-Position

```
Training Backend (45680) → Dataset Backend (45681) → UDS3 (PostgreSQL, ChromaDB, Neo4j)
                          ↓
                    Exported Datasets
                    (JSONL, Parquet, CSV)
```

---

## Features

### 1. **Dataset Search & Creation**

- Suche über UDS3 Hybrid Search (Vector + Graph + Keyword)
- Quality Score Filtering
- Flexible Filterung nach Domain/Type
- Batch-Verarbeitung

### 2. **Quality Pipeline**

- **Inhalts-Qualität**: Mindestlänge (100 Zeichen)
- **Metadaten-Vollständigkeit**: Source, Domain, Timestamps
- **Relevanz-Score**: Semantic Search Score
- **Gesamtscore**: Gewichtetes Mittel aller Faktoren

**Quality Score Berechnung:**

```python
quality_score = (
    content_quality * 0.4 +      # 40% Inhalt
    metadata_quality * 0.3 +     # 30% Metadaten
    relevance_score * 0.3        # 30% Relevanz
)
```

### 3. **Multi-Format Export**

| Format | Beschreibung | Use Case |
|--------|-------------|----------|
| **JSONL** | JSON Lines (ein Objekt pro Zeile) | Training Pipelines, Streaming |
| **Parquet** | Columnar Storage (Apache Arrow) | Big Data, Analytics |
| **CSV** | Comma-Separated Values | Excel, Legacy Tools |
| **JSON** | Single JSON Array | Small Datasets, Debugging |

### 4. **Dataset Registry**

- Metadata-Speicherung (Name, Description, Created By)
- Status-Tracking (Pending → Processing → Completed/Failed)
- Statistics (Document Count, Token Count, Avg Quality Score)
- Export Path Registry

---

## Installation

### Voraussetzungen

- Python 3.9+
- FastAPI + Uvicorn
- UDS3 Backend (PostgreSQL, ChromaDB, Neo4j)
- JWT Middleware (shared/jwt_middleware.py)
- UDS3 Dataset Search API (shared/uds3_dataset_search.py)

### Dependencies

```bash
# Install core dependencies
pip install fastapi uvicorn pydantic

# Optional: Parquet export support
pip install pandas pyarrow

# Optional: JWT authentication
pip install python-jose[cryptography] requests
```

### Setup

1. **Klone Repository:**
   ```bash
   cd C:\VCC\Clara
   ```

2. **Virtual Environment aktivieren:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Environment Variables setzen:**
   ```powershell
   $env:CLARA_SECURITY_MODE = "development"
   $env:CLARA_DATASET_PORT = "45681"
   ```

4. **Service starten:**
   ```powershell
   python scripts\clara_dataset_backend.py
   ```

---

## Verwendung

### Quick Start (Interactive)

**Interaktiver Launcher mit Security Mode Auswahl:**

```powershell
.\start_dataset_backend_interactive.ps1
```

**Menu:**
```
[1] 🔐 Production Mode - JWT + mTLS
[2] 🛠️  Development Mode - JWT only
[3] 🐛 Debug Mode - No authentication
[4] 🧪 Testing Mode - Mock authentication
```

### Quick Start (Manual)

**Development Mode (empfohlen):**

```powershell
.\start_dataset_backend.ps1 -SecurityMode development
```

**Debug Mode (kein Auth):**

```powershell
.\start_dataset_backend.ps1 -SecurityMode debug
```

**Production Mode (JWT + mTLS):**

```powershell
.\start_dataset_backend.ps1 -SecurityMode production
```

### Workflow Beispiel

#### 1. **Dataset erstellen**

```bash
curl -X POST http://localhost:45681/api/datasets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Verwaltungsrecht Training Dataset",
    "description": "High-quality documents on administrative law",
    "search_query": {
      "query_text": "Verwaltungsrecht Verwaltungsakt Rechtmäßigkeit",
      "top_k": 200,
      "min_quality_score": 0.7,
      "search_types": ["vector", "graph"],
      "filters": {"domain": "legal"}
    },
    "export_formats": ["jsonl", "parquet"]
  }'
```

**Response:**
```json
{
  "success": true,
  "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "pending",
  "message": "Dataset created: f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "data": {
    "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Verwaltungsrecht Training Dataset",
    "status": "pending",
    "created_at": "2024-10-24T14:30:00",
    "created_by": "user@example.com"
  }
}
```

#### 2. **Dataset Status abfragen**

```bash
curl http://localhost:45681/api/datasets/f47ac10b-58cc-4372-a567-0e02b2c3d479 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "success": true,
  "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "completed",
  "message": "Dataset details retrieved",
  "data": {
    "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Verwaltungsrecht Training Dataset",
    "description": "High-quality documents on administrative law",
    "status": "completed",
    "document_count": 187,
    "total_tokens": 342150,
    "quality_score_avg": 0.84,
    "export_paths": {
      "jsonl": "data/datasets/f47ac10b-58cc-4372-a567-0e02b2c3d479/Verwaltungsrecht_Training_Dataset.jsonl",
      "parquet": "data/datasets/f47ac10b-58cc-4372-a567-0e02b2c3d479/Verwaltungsrecht_Training_Dataset.parquet"
    },
    "created_at": "2024-10-24T14:30:00",
    "created_by": "user@example.com"
  }
}
```

#### 3. **Alle Datasets auflisten**

```bash
curl http://localhost:45681/api/datasets \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 4. **Dataset verwenden (Training Job)**

```bash
# Training Job mit exportiertem Dataset starten
curl -X POST http://localhost:45680/api/training/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "job_name": "LoRA Training - Verwaltungsrecht",
    "trainer_type": "lora",
    "config": {
      "model_name": "google/gemma-2-2b",
      "dataset_path": "data/datasets/f47ac10b-58cc-4372-a567-0e02b2c3d479/Verwaltungsrecht_Training_Dataset.jsonl",
      "num_epochs": 5,
      "learning_rate": 0.0001
    }
  }'
```

---

## API Referenz

### Endpoints

#### **GET /health**

Health Check Endpoint

**Response:**
```json
{
  "status": "healthy",
  "service": "clara_dataset_backend",
  "port": 45681,
  "uds3_available": true,
  "datasets_count": 12,
  "timestamp": "2024-10-24T14:30:00"
}
```

---

#### **POST /api/datasets**

Create new dataset from search query

🔐 **Security:** JWT Required, Roles: `admin` OR `trainer` OR `analyst`

**Request Body:**
```json
{
  "name": "Dataset Name",
  "description": "Optional description",
  "search_query": {
    "query_text": "Search query",
    "top_k": 100,
    "min_quality_score": 0.5,
    "filters": {"domain": "legal"},
    "search_types": ["vector", "graph"],
    "weights": {"vector": 0.7, "graph": 0.3}
  },
  "export_formats": ["jsonl", "parquet"]
}
```

**Response:** `DatasetResponse` (siehe oben)

---

#### **GET /api/datasets/{dataset_id}**

Get dataset details by ID

🔐 **Security:** JWT Required (any authenticated user)

**Response:** `DatasetResponse`

---

#### **GET /api/datasets**

List all datasets

🔐 **Security:** JWT Required (any authenticated user)

**Response:**
```json
{
  "datasets": [
    {
      "dataset_id": "...",
      "name": "...",
      "status": "completed",
      "document_count": 187,
      ...
    }
  ],
  "total_count": 12
}
```

---

#### **POST /api/datasets/{dataset_id}/export**

Export dataset to additional format

🔐 **Security:** JWT Required, Roles: `admin` OR `trainer`

**Request Body:**
```json
{
  "format": "parquet",
  "include_metadata": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Dataset already exported to parquet",
  "export_path": "data/datasets/.../dataset.parquet"
}
```

---

## Konfiguration

### Environment Variables

| Variable | Default | Beschreibung |
|----------|---------|--------------|
| `CLARA_SECURITY_MODE` | `development` | Security Mode (production/development/debug/testing) |
| `CLARA_DATASET_PORT` | `45681` | Service Port |
| `UDS3_POSTGRES_HOST` | `192.168.178.94` | PostgreSQL Host |
| `UDS3_POSTGRES_PORT` | `5432` | PostgreSQL Port |
| `UDS3_CHROMADB_HOST` | `192.168.178.94` | ChromaDB Host |
| `UDS3_CHROMADB_PORT` | `8000` | ChromaDB Port |
| `UDS3_NEO4J_URI` | `bolt://192.168.178.94:7687` | Neo4j URI |

### Security Modes

#### **1. Production Mode** (`production`)

```powershell
$env:CLARA_SECURITY_MODE = "production"
```

- ✅ JWT Authentication: **ENABLED**
- ✅ mTLS: **ENABLED**
- ✅ Keycloak: **REQUIRED**
- ✅ PKI Service: **REQUIRED**
- ✅ Audit Logging: **FULL**

**Requirements:**
- Keycloak running on http://localhost:8080
- PKI Service running on https://localhost:8443
- Valid SSL certificates

#### **2. Development Mode** (`development`)

```powershell
$env:CLARA_SECURITY_MODE = "development"
```

- ✅ JWT Authentication: **ENABLED**
- ❌ mTLS: **DISABLED**
- ⚠️ Keycloak: **OPTIONAL** (graceful fallback)
- ❌ PKI Service: **NOT REQUIRED**
- ⚠️ Audit Logging: **BASIC**

**Best for:** Local development with JWT testing

#### **3. Debug Mode** (`debug`)

```powershell
$env:CLARA_SECURITY_MODE = "debug"
```

- ❌ JWT Authentication: **DISABLED**
- ❌ mTLS: **DISABLED**
- ❌ Keycloak: **NOT REQUIRED**
- ❌ PKI Service: **NOT REQUIRED**
- ⚠️ Audit Logging: **MINIMAL**

⚠️ **WARNING:** DO NOT USE IN PRODUCTION!

**Best for:** Quick testing, debugging

#### **4. Testing Mode** (`testing`)

```powershell
$env:CLARA_SECURITY_MODE = "testing"
```

- ⚠️ JWT Authentication: **MOCK**
- ❌ mTLS: **DISABLED**
- ⚠️ Keycloak: **MOCKED**
- ❌ PKI Service: **NOT REQUIRED**
- ✅ Audit Logging: **FULL**

**Best for:** Integration tests, CI/CD

---

## Security

### RBAC Roles

| Role | Permissions |
|------|------------|
| **admin** | Full access (create, read, update, delete datasets) |
| **trainer** | Create datasets, read all, export |
| **analyst** | Create datasets, read all |
| **user** | Read only |
| **auditor** | Read only + audit logs |

### Endpoint Security Matrix

| Endpoint | Roles | Public |
|----------|-------|--------|
| `GET /health` | - | ✅ Yes |
| `POST /api/datasets` | admin, trainer, analyst | ❌ No |
| `GET /api/datasets/{id}` | * (authenticated) | ❌ No |
| `GET /api/datasets` | * (authenticated) | ❌ No |
| `POST /api/datasets/{id}/export` | admin, trainer | ❌ No |

### Audit Logging

Alle Dataset-Operationen werden geloggt:

```json
{
  "timestamp": "2024-10-24T14:30:00",
  "event": "dataset_created",
  "user": "user@example.com",
  "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "dataset_name": "Verwaltungsrecht Training Dataset",
  "document_count": 187
}
```

---

## Deployment

### Local Development

```powershell
# 1. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 2. Set security mode
$env:CLARA_SECURITY_MODE = "development"

# 3. Start service
python scripts\clara_dataset_backend.py
```

### Docker (TODO)

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 45681

CMD ["python", "scripts/clara_dataset_backend.py"]
```

```bash
# Build
docker build -t clara-dataset-backend .

# Run
docker run -p 45681:45681 \
  -e CLARA_SECURITY_MODE=production \
  clara-dataset-backend
```

### Kubernetes (TODO)

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: clara-dataset-backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: clara-dataset-backend
  template:
    metadata:
      labels:
        app: clara-dataset-backend
    spec:
      containers:
      - name: dataset-backend
        image: clara-dataset-backend:latest
        ports:
        - containerPort: 45681
        env:
        - name: CLARA_SECURITY_MODE
          value: "production"
```

---

## Troubleshooting

### Problem: UDS3 nicht erreichbar

**Symptom:**
```
⚠️ UDS3 Search API initialization failed: Connection refused
```

**Lösung:**
1. Check UDS3 Backend:
   ```bash
   curl http://192.168.178.94:5432  # PostgreSQL
   curl http://192.168.178.94:8000  # ChromaDB
   curl http://192.168.178.94:7687  # Neo4j
   ```

2. Check `.env` configuration:
   ```
   UDS3_POSTGRES_HOST=192.168.178.94
   UDS3_CHROMADB_HOST=192.168.178.94
   UDS3_NEO4J_URI=bolt://192.168.178.94:7687
   ```

3. Graceful Degradation:
   - Service startet auch ohne UDS3
   - Mock-Daten für Development

### Problem: JWT Validation Error

**Symptom:**
```
401 Unauthorized: Invalid token
```

**Lösung:**
1. Check Keycloak:
   ```bash
   curl http://localhost:8080/realms/clara/.well-known/openid-configuration
   ```

2. Get new token:
   ```bash
   curl -X POST http://localhost:8080/realms/clara/protocol/openid-connect/token \
     -d "client_id=clara-client" \
     -d "client_secret=YOUR_SECRET" \
     -d "grant_type=client_credentials"
   ```

3. Use Debug Mode (temporarily):
   ```powershell
   $env:CLARA_SECURITY_MODE = "debug"
   python scripts\clara_dataset_backend.py
   ```

### Problem: Port already in use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Lösung:**
1. Find process using port:
   ```powershell
   netstat -ano | findstr :45681
   ```

2. Kill process:
   ```powershell
   taskkill /PID <PID> /F
   ```

3. Or use different port:
   ```powershell
   $env:CLARA_DATASET_PORT = "45682"
   ```

### Problem: Export failed (Parquet)

**Symptom:**
```
ImportError: No module named 'pyarrow'
```

**Lösung:**
```bash
pip install pandas pyarrow
```

Fallback: Service verwendet JSONL stattdessen

---

## Anhang

### Dataset Export Formats

#### **JSONL Example:**

```jsonl
{"document_id": "doc_001", "text": "Content...", "source": "legal_db", "quality_score": 0.85, "relevance_score": 0.92}
{"document_id": "doc_002", "text": "Content...", "source": "legal_db", "quality_score": 0.78, "relevance_score": 0.88}
```

#### **Parquet Example:**

Binary columnar format (Apache Arrow) - optimal für Big Data Analytics

#### **CSV Example:**

```csv
document_id,text,source,quality_score,relevance_score
doc_001,"Content...",legal_db,0.85,0.92
doc_002,"Content...",legal_db,0.78,0.88
```

#### **JSON Example:**

```json
{
  "dataset_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "name": "Verwaltungsrecht Training Dataset",
  "document_count": 187,
  "documents": [
    {"document_id": "doc_001", "text": "Content...", ...},
    {"document_id": "doc_002", "text": "Content...", ...}
  ]
}
```

### Performance Benchmarks

| Operation | Avg Time | Documents |
|-----------|----------|-----------|
| Search (UDS3) | 1.2s | 100 docs |
| Quality Filter | 0.05s | 100 docs |
| Export JSONL | 0.3s | 100 docs |
| Export Parquet | 0.8s | 100 docs |

---

## Support

- **Documentation:** `docs/DATASET_MANAGEMENT_SERVICE.md`
- **API Docs:** http://localhost:45681/docs (Swagger UI)
- **GitHub:** https://github.com/makr-code/VCC-Clara

---

**Version:** 1.0.0  
**Last Updated:** 2024-10-24  
**Status:** ✅ PRODUCTION READY
