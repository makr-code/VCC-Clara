# VCC-Clara Technical Implementation Roadmap

**Erstellt:** 2025-11-23  
**Version:** 1.0  
**Status:** 🚀 Implementation Guide  
**Verantwortlich:** Technical Lead  
**Bezugsdokument:** VCC_CLARA_WEITERENTWICKLUNGSSTRATEGIE.md

---

## Executive Summary

Dieses Dokument übersetzt die strategischen Ziele aus der Weiterentwicklungsstrategie in konkrete, umsetzbare technische Tasks mit Zeitplänen, Abhängigkeiten und Akzeptanzkriterien.

---

## Phase 1: Stabilisierung & Foundation (Q4 2025 - Q1 2026)

### Sprint 1-2: Dokumentations-Gap Closure (2 Wochen)

#### Task 1.1: File Path Corrections
**Verantwortlich:** Tech Writer + Developer  
**Aufwand:** 3 Tage  
**Priorität:** 🔴 CRITICAL

**Zu korrigierende Dateien:**
- [ ] Update `shared/auth/jwt_middleware.py` → `shared/auth/middleware.py` (alle Referenzen)
- [ ] Update `shared/database/uds3_dataset_search.py` → `shared/database/dataset_search.py`
- [ ] Fix `config/config.py` → `config/__init__.py` Referenzen
- [ ] Port-Referenzen: Hardcoded → `config.training_port`, `config.dataset_port`

**Betroffene Dokumentation:**
```bash
# Find & Replace in docs/
grep -r "jwt_middleware.py" docs/
grep -r "uds3_dataset_search.py" docs/
grep -r "config/config.py" docs/
grep -r "Port 45680" docs/
grep -r "Port 45681" docs/
```

**Akzeptanzkriterien:**
- ✅ Alle File-Path-Referenzen korrekt
- ✅ Keine Non-Existenten Files in Dokumentation
- ✅ Legacy-Code klar als "archived" markiert

---

#### Task 1.2: UDS3 Integration Status Documentation
**Verantwortlich:** Developer + Tech Writer  
**Aufwand:** 2 Tage  
**Priorität:** 🔴 CRITICAL

**Schritte:**
1. Code-Analyse: `backend/datasets/manager.py` → `UDS3_AVAILABLE` Flag
2. Testen: System mit/ohne UDS3
3. Dokumentieren:
   - [ ] UDS3_STATUS.md erweitern
   - [ ] Feature-Matrix erstellen (mit/ohne UDS3)
   - [ ] Installation-Guide für UDS3
   - [ ] Graceful-Degradation-Behaviour dokumentieren

**Code zu analysieren:**
```python
# backend/datasets/manager.py
from .uds3_integration import UDS3_AVAILABLE

if UDS3_AVAILABLE:
    # Full features
else:
    # Fallback behavior
```

**Deliverables:**
- [ ] Updated UDS3_STATUS.md
- [ ] Feature Comparison Table
- [ ] Installation Guide
- [ ] Troubleshooting Section

---

#### Task 1.3: API Reference Completion
**Verantwortlich:** Developer  
**Aufwand:** 3 Tage  
**Priorität:** 🟡 HIGH

**OpenAPI 3.0 Spec erstellen:**
```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: VCC-Clara API
  version: 2.0.0
  description: Comprehensive API for VCC-Clara AI System

servers:
  - url: http://localhost:45680
    description: Training Backend
  - url: http://localhost:45681
    description: Dataset Backend

paths:
  /api/training/jobs:
    post:
      summary: Create training job
      # ... detailed spec
```

**Tasks:**
- [ ] OpenAPI Spec für Training Backend (8 Endpoints)
- [ ] OpenAPI Spec für Dataset Backend (6 Endpoints)
- [ ] Code Examples (cURL, Python, JavaScript)
- [ ] Swagger UI Integration
- [ ] ReDoc Integration
- [ ] Postman Collection Generation

**Akzeptanzkriterien:**
- ✅ Alle Endpoints dokumentiert
- ✅ Request/Response Schemas vollständig
- ✅ Mindestens 2 Code Examples pro Endpoint
- ✅ Swagger UI funktioniert

---

### Sprint 3-4: Test Coverage Improvement (2 Wochen)

#### Task 1.4: Unit Test Expansion
**Verantwortlich:** QA Engineer + Developers  
**Aufwand:** 5 Tage  
**Priorität:** 🔴 CRITICAL

**Current Coverage:** 60% (laut README.md)  
**Target:** 80%+

**Priorität Module (nach Coverage Gap):**
1. `backend/training/` (aktuell ~50% → Ziel: >80%)
2. `backend/datasets/` (aktuell ~55% → Ziel: >80%)
3. `shared/auth/` (aktuell ~40% → Ziel: >85%)
4. `shared/database/` (aktuell ~45% → Ziel: >80%)

**Test Framework Setup:**
```python
# pytest.ini (erweitern)
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Coverage Konfiguration
addopts = 
    --cov=backend
    --cov=shared
    --cov=frontend
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

**Zu erstellende Tests:**
- [ ] `tests/unit/backend/training/test_job_manager.py` (20+ Tests)
- [ ] `tests/unit/backend/datasets/test_manager.py` (15+ Tests)
- [ ] `tests/unit/shared/auth/test_middleware.py` (10+ Tests)
- [ ] `tests/unit/shared/database/test_dataset_search.py` (12+ Tests)
- [ ] `tests/unit/config/test_all_configs.py` (8+ Tests)

**Coverage-Metriken:**
```bash
# Daily ausführen
pytest --cov=backend --cov=shared --cov-report=html
open htmlcov/index.html

# CI Integration
pytest --cov --cov-fail-under=80
```

---

#### Task 1.5: Integration Tests
**Verantwortlich:** QA Engineer  
**Aufwand:** 4 Tage  
**Priorität:** 🟡 HIGH

**Integration Test Scenarios:**

1. **Training Flow (End-to-End)**
```python
# tests/integration/test_training_flow.py
async def test_complete_training_flow():
    # 1. Create job
    job = await client.post("/api/training/jobs", json=job_config)
    
    # 2. Wait for completion
    await wait_for_job_completion(job["id"])
    
    # 3. Verify model artifacts
    assert model_exists(job["output_dir"])
    
    # 4. Cleanup
    await client.delete(f"/api/training/jobs/{job['id']}")
```

2. **Dataset Flow (End-to-End)**
```python
# tests/integration/test_dataset_flow.py
async def test_dataset_creation_and_export():
    # 1. Create dataset
    dataset = await client.post("/api/datasets", json=dataset_config)
    
    # 2. Add documents
    await client.post(f"/api/datasets/{dataset['id']}/documents", ...)
    
    # 3. Export
    export = await client.post(f"/api/datasets/{dataset['id']}/export", 
                                json={"format": "jsonl"})
    
    # 4. Verify export
    assert export_file_valid(export["path"])
```

3. **Authentication Flow**
```python
# tests/integration/test_auth_flow.py
async def test_jwt_authentication():
    # 1. Obtain token
    token = await get_jwt_token(username, password)
    
    # 2. Access protected endpoint
    response = await client.get("/api/training/jobs", 
                                 headers={"Authorization": f"Bearer {token}"})
    
    # 3. Verify access
    assert response.status_code == 200
```

**Test-Umgebung:**
- [ ] Test-Database Setup (PostgreSQL in Docker)
- [ ] Mock UDS3 Services
- [ ] Test-Fixtures für Training Data
- [ ] Cleanup-Mechanismen

---

#### Task 1.6: E2E Tests (Frontend)
**Verantwortlich:** QA Engineer  
**Aufwand:** 3 Tage  
**Priorität:** 🟢 MEDIUM

**Playwright für tkinter Testing (Alternative: manuell)**

Da tkinter-GUIs schwer automatisiert testbar sind:

**Option A: Manual Test Scripts**
```python
# tests/e2e/manual_test_scenarios.md
## Test Scenario 1: Training Job Creation
1. Open Training Frontend
2. Click "New Job"
3. Fill form...
4. Expected: Job appears in list
```

**Option B: Unit-Test GUI Components**
```python
# tests/unit/frontend/test_training_view.py
def test_job_creation_ui():
    view = TrainingView()
    view.create_job_button.invoke()
    assert view.job_form_visible()
```

**E2E Test Cases:**
- [ ] Training Job Creation (Admin Frontend)
- [ ] Dataset Export (Data Prep Frontend)
- [ ] Service Control (Admin Frontend)
- [ ] Real-Time Job Updates (WebSocket)

---

### Sprint 5-6: CI/CD Pipeline (2 Wochen)

#### Task 1.7: GitHub Actions Setup
**Verantwortlich:** DevOps Engineer  
**Aufwand:** 4 Tage  
**Priorität:** 🟡 HIGH

**Workflow-Struktur:**
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install black flake8 mypy
      - name: Black
        run: black --check .
      - name: Flake8
        run: flake8 backend/ shared/ frontend/
      - name: MyPy
        run: mypy backend/ shared/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Bandit
        run: bandit -r backend/ shared/
      - name: Run Safety
        run: safety check
      - name: Snyk Security Scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements_api.txt
      - name: Run tests
        run: pytest --cov --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    runs-on: ubuntu-latest
    needs: [lint, security, test]
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker images
        run: |
          docker build -t vcc-clara/training:${{ github.sha }} -f Dockerfile.training .
          docker build -t vcc-clara/datasets:${{ github.sha }} -f Dockerfile.datasets .
      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push vcc-clara/training:${{ github.sha }}
          docker push vcc-clara/datasets:${{ github.sha }}
```

**Deliverables:**
- [ ] `.github/workflows/ci.yml`
- [ ] `.github/workflows/cd-dev.yml`
- [ ] `.github/workflows/cd-staging.yml`
- [ ] `.github/workflows/cd-prod.yml`
- [ ] Docker Registry Setup (GitHub Container Registry)

---

#### Task 1.8: Dockerfile Optimization
**Verantwortlich:** DevOps Engineer  
**Aufwand:** 2 Tage  
**Priorität:** 🟢 MEDIUM

**Multi-Stage Build:**
```dockerfile
# Dockerfile.training
# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

# Security: Non-root user
RUN useradd -m -u 1000 clara && \
    mkdir -p /app && \
    chown -R clara:clara /app

WORKDIR /app
USER clara

# Copy dependencies
COPY --from=builder /root/.local /home/clara/.local
ENV PATH=/home/clara/.local/bin:$PATH

# Copy application
COPY --chown=clara:clara backend/training ./backend/training
COPY --chown=clara:clara shared ./shared
COPY --chown=clara:clara config ./config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:45680/health || exit 1

EXPOSE 45680

CMD ["python", "-m", "backend.training.app"]
```

**Optimization Goals:**
- ✅ Image Size: <500MB (current: ???)
- ✅ Build Time: <5 minutes
- ✅ Security: Non-root user
- ✅ Caching: Layer optimization

---

### Sprint 7-8: Legacy Code Cleanup (2 Wochen)

#### Task 1.9: Archive Documentation
**Verantwortlich:** Tech Writer + Developer  
**Aufwand:** 2 Tage  
**Priorität:** 🟢 MEDIUM

**Archive Directory Documentation:**
```markdown
# archive/legacy_backends/README.md

# Legacy Backends - Archived Components

**Status:** ⚠️ DEPRECATED - Do not use for new development  
**Date Archived:** 2025-10-15  
**Reason:** Replaced by new microservices architecture

## Components

### 1. jwt_middleware.py
**Replaced by:** `shared/auth/middleware.py`  
**Reason:** Refactored for better modularity

### 2. uds3_dataset_search.py
**Replaced by:** `shared/database/dataset_search.py`  
**Reason:** Renamed for consistency

### 3. clara_dataset_backend.py
**Replaced by:** `backend/datasets/app.py`  
**Reason:** New microservices architecture

### 4. clara_training_backend.py
**Replaced by:** `backend/training/app.py`  
**Reason:** New microservices architecture

## Migration Guide

See: [MIGRATION_GUIDE.md](../../docs/MIGRATION_GUIDE.md)
```

**Tasks:**
- [ ] Create `archive/legacy_backends/README.md`
- [ ] Document each legacy component
- [ ] Link to new implementations
- [ ] Migration examples

---

#### Task 1.10: Batch Processor Consolidation
**Verantwortlich:** Developer  
**Aufwand:** 3 Tage  
**Priorität:** 🟢 MEDIUM

**Current State:**
```
scripts/
├── clara_smart_batch_processor.py
├── clara_smart_batch_processor_fixed.py
├── clara_smart_batch_processor_corrected.py
├── clara_smart_batch_processor_simple.py
└── clara_intelligent_batch_processor.py
```

**Goal:** Consolidate zu EINEM Batch Processor

**Analysis:**
```bash
# Compare implementations
diff clara_smart_batch_processor.py clara_intelligent_batch_processor.py
diff clara_smart_batch_processor_fixed.py clara_smart_batch_processor_corrected.py
```

**Decision Matrix:**
| Feature | smart | intelligent | fixed | corrected | simple |
|---------|-------|-------------|-------|-----------|--------|
| Dedup | ✅ | ✅ | ✅ | ✅ | ❌ |
| SQLite Cache | ✅ | ✅ | ✅ | ✅ | ❌ |
| PDF Support | ✅ | ✅ | ✅ | ✅ | ❌ |
| Error Handling | ⚠️ | ✅ | ✅ | ✅ | ⚠️ |
| Tests | ❌ | ❌ | ❌ | ❌ | ❌ |

**Recommendation:** Keep `clara_intelligent_batch_processor.py`, archive others

**Tasks:**
- [ ] Feature comparison analysis
- [ ] Choose canonical version
- [ ] Add comprehensive tests
- [ ] Archive others with deprecation notice
- [ ] Update documentation

---

## Phase 2: Cloud-Native Transformation (Q2-Q3 2026)

### Sprint 9-12: Kubernetes Migration (4 Wochen)

#### Task 2.1: Helm Chart Creation
**Verantwortlich:** DevOps Engineer  
**Aufwand:** 1 Woche  
**Priorität:** 🔴 CRITICAL

**Helm Chart Structure:**
```
vcc-clara/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-staging.yaml
├── values-prod.yaml
└── templates/
    ├── training/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── configmap.yaml
    │   └── hpa.yaml
    ├── datasets/
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── configmap.yaml
    │   └── hpa.yaml
    ├── postgres/
    │   ├── statefulset.yaml
    │   ├── service.yaml
    │   └── pvc.yaml
    └── ingress.yaml
```

**Sample Deployment:**
```yaml
# templates/training/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "vcc-clara.fullname" . }}-training
  labels:
    {{- include "vcc-clara.labels" . | nindent 4 }}
    component: training
spec:
  replicas: {{ .Values.training.replicaCount }}
  selector:
    matchLabels:
      {{- include "vcc-clara.selectorLabels" . | nindent 6 }}
      component: training
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/training/configmap.yaml") . | sha256sum }}
      labels:
        {{- include "vcc-clara.selectorLabels" . | nindent 8 }}
        component: training
    spec:
      serviceAccountName: {{ include "vcc-clara.serviceAccountName" . }}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: training
        image: "{{ .Values.training.image.repository }}:{{ .Values.training.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.training.image.pullPolicy }}
        ports:
        - name: http
          containerPort: 45680
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          {{- toYaml .Values.training.resources | nindent 12 }}
        env:
        - name: CLARA_SECURITY_MODE
          value: {{ .Values.security.mode }}
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {{ include "vcc-clara.fullname" . }}-db
              key: url
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: models
          mountPath: /app/models
      volumes:
      - name: config
        configMap:
          name: {{ include "vcc-clara.fullname" . }}-training-config
      - name: models
        persistentVolumeClaim:
          claimName: {{ include "vcc-clara.fullname" . }}-models
```

**HPA (Horizontal Pod Autoscaler):**
```yaml
# templates/training/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "vcc-clara.fullname" . }}-training
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "vcc-clara.fullname" . }}-training
  minReplicas: {{ .Values.training.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.training.autoscaling.maxReplicas }}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {{ .Values.training.autoscaling.targetCPUUtilizationPercentage }}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {{ .Values.training.autoscaling.targetMemoryUtilizationPercentage }}
```

---

#### Task 2.2: Service Mesh (Istio)
**Verantwortlich:** DevOps Engineer  
**Aufwand:** 1 Woche  
**Priorität:** 🟡 HIGH

**Istio Configuration:**
```yaml
# templates/istio/virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: vcc-clara-training
spec:
  hosts:
  - training.vcc-clara.svc.cluster.local
  http:
  - match:
    - uri:
        prefix: /api/training
    route:
    - destination:
        host: training.vcc-clara.svc.cluster.local
        port:
          number: 45680
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset,connect-failure
    timeout: 10s
```

**mTLS Policy:**
```yaml
# templates/istio/peer-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: vcc-clara-mtls
spec:
  selector:
    matchLabels:
      app: vcc-clara
  mtls:
    mode: STRICT
```

---

### Sprint 13-16: Managed Services Integration (4 Wochen)

#### Task 2.3: PostgreSQL High Availability Setup
**Verantwortlich:** Database Admin + DevOps  
**Aufwand:** 1 Woche  
**Priorität:** 🟡 HIGH

**On-Premise HA Setup:**

1. **PostgreSQL HA Stack**
   - **Patroni** für automatisches Failover
   - **HAProxy/PgBouncer** für Connection Pooling
   - **Streaming Replication** (Synchronous/Asynchronous)
   - 3-Node Cluster (1 Primary, 2 Standby)

2. **Data Migration**
```bash
# 1. Backup current data
pg_dump -h localhost -U postgres -d clara > clara_backup.sql

# 2. Setup Patroni cluster
# Install Patroni on all nodes
pip install patroni[etcd]

# 3. Restore to HA cluster
psql -h patroni-cluster-vip -U postgres -d clara < clara_backup.sql

# 4. Verify replication
psql -h patroni-cluster-vip -U postgres -c "SELECT * FROM pg_stat_replication;"
```

3. **Connection Pooling (PgBouncer)**
```yaml
# templates/pgbouncer/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: pgbouncer
        image: pgbouncer/pgbouncer:1.21
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: url
```

---

#### Task 2.4: On-Premise Object Storage (MinIO)
**Verantwortlich:** DevOps Engineer  
**Aufwand:** 3 Tage  
**Priorität:** 🟢 MEDIUM

**Use Cases:**
- Model Storage
- Training Data
- Exports
- Backups

**MinIO Setup:**
```yaml
# MinIO Deployment (S3-kompatibel, on-premise)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: minio
spec:
  serviceName: minio
  replicas: 4  # Distributed mode
  template:
    spec:
      containers:
      - name: minio
        image: minio/minio:latest
        args:
        - server
        - http://minio-{0...3}.minio.vcc-clara.svc.cluster.local/data
        env:
        - name: MINIO_ROOT_USER
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: root-user
        - name: MINIO_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: minio-credentials
              key: root-password
```

**Implementation:**
```python
# shared/storage/object_storage.py
import boto3
from typing import BinaryIO

class ObjectStorage:
    def __init__(self, bucket: str, endpoint_url: str = None):
        # S3-compatible client (works with MinIO)
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint_url or 'http://minio:9000',
            aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('MINIO_SECRET_KEY')
        )
        self.bucket = bucket
    
    def upload_model(self, model_path: str, key: str):
        self.s3.upload_file(model_path, self.bucket, key)
    
    def download_model(self, key: str, destination: str):
        self.s3.download_file(self.bucket, key, destination)
    
    def upload_fileobj(self, fileobj: BinaryIO, key: str):
        self.s3.upload_fileobj(fileobj, self.bucket, key)
```

**Lifecycle Policies:**
```json
{
  "Rules": [
    {
      "Id": "ArchiveOldModels",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    },
    {
      "Id": "DeleteOldExports",
      "Status": "Enabled",
      "Expiration": {
        "Days": 30
      },
      "Filter": {
        "Prefix": "exports/"
      }
    }
  ]
}
```

---

## Phase 3: Advanced AI & MLOps (Q4 2026 - Q1 2027)

### Sprint 17-20: MLOps Pipeline (4 Wochen)

#### Task 3.1: MLflow Integration
**Verantwortlich:** ML Engineer  
**Aufwand:** 1 Woche  
**Priorität:** 🔴 CRITICAL

**MLflow Setup:**
```python
# backend/training/mlflow_tracker.py
import mlflow
from mlflow.tracking import MlflowClient

class TrainingTracker:
    def __init__(self, experiment_name: str):
        mlflow.set_experiment(experiment_name)
        self.client = MlflowClient()
    
    def start_run(self, run_name: str, tags: dict):
        return mlflow.start_run(run_name=run_name, tags=tags)
    
    def log_params(self, params: dict):
        mlflow.log_params(params)
    
    def log_metrics(self, metrics: dict, step: int):
        mlflow.log_metrics(metrics, step=step)
    
    def log_model(self, model, artifact_path: str):
        mlflow.pytorch.log_model(model, artifact_path)
    
    def log_dataset(self, dataset_path: str):
        mlflow.log_artifact(dataset_path, "datasets")
```

**Training Integration:**
```python
# backend/training/trainer.py
from .mlflow_tracker import TrainingTracker

class LoRATrainer:
    def __init__(self, config):
        self.tracker = TrainingTracker(experiment_name=config.experiment_name)
    
    def train(self):
        with self.tracker.start_run(run_name=f"lora-{self.config.domain}", 
                                     tags={"domain": self.config.domain}):
            # Log hyperparameters
            self.tracker.log_params({
                "learning_rate": self.config.learning_rate,
                "batch_size": self.config.batch_size,
                "lora_rank": self.config.lora_rank,
                # ...
            })
            
            # Training loop
            for epoch in range(self.config.epochs):
                metrics = self.train_epoch()
                self.tracker.log_metrics(metrics, step=epoch)
            
            # Log final model
            self.tracker.log_model(self.model, "lora_adapter")
```

---

#### Task 3.2: Model Registry
**Verantwortlich:** ML Engineer  
**Aufwand:** 3 Tage  
**Priorität:** 🟡 HIGH

**Model Registry Integration:**
```python
# backend/training/model_registry.py
import mlflow
from mlflow.tracking import MlflowClient

class ModelRegistry:
    def __init__(self):
        self.client = MlflowClient()
    
    def register_model(self, run_id: str, model_name: str, tags: dict):
        """Register model from MLflow run"""
        model_uri = f"runs:/{run_id}/lora_adapter"
        result = mlflow.register_model(model_uri, model_name)
        
        # Add tags
        for key, value in tags.items():
            self.client.set_model_version_tag(
                name=model_name,
                version=result.version,
                key=key,
                value=value
            )
        
        return result
    
    def promote_to_production(self, model_name: str, version: int):
        """Promote model version to production"""
        self.client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage="Production"
        )
    
    def get_production_model(self, model_name: str):
        """Get current production model"""
        versions = self.client.get_latest_versions(
            name=model_name,
            stages=["Production"]
        )
        return versions[0] if versions else None
```

---

#### Task 3.3: Feature Store (Feast)
**Verantwortlich:** ML Engineer  
**Aufwand:** 1 Woche  
**Priorität:** 🟢 MEDIUM

**Feast Configuration:**
```yaml
# feature_repo/feature_store.yaml
project: vcc_clara
registry: s3://vcc-clara-features/registry.db
provider: aws
online_store:
  type: redis
  connection_string: redis://redis:6379
offline_store:
  type: file
  path: s3://vcc-clara-features/offline
```

**Feature Definitions:**
```python
# feature_repo/features.py
from feast import Entity, Feature, FeatureView, ValueType
from feast.data_source import FileSource

# Entity
document = Entity(
    name="document",
    value_type=ValueType.STRING,
    description="Document identifier"
)

# Data source
document_source = FileSource(
    path="s3://vcc-clara-features/documents.parquet",
    event_timestamp_column="timestamp"
)

# Feature view
document_features = FeatureView(
    name="document_features",
    entities=["document"],
    ttl=timedelta(days=90),
    features=[
        Feature(name="domain", dtype=ValueType.STRING),
        Feature(name="length", dtype=ValueType.INT64),
        Feature(name="complexity_score", dtype=ValueType.FLOAT),
    ],
    online=True,
    input=document_source,
    tags={"team": "ml"}
)
```

---

### Sprint 21-24: Advanced Training (4 Wochen)

#### Task 3.4: DoRA Implementation
**Verantwortlich:** ML Engineer  
**Aufwand:** 1 Woche  
**Priorität:** 🟡 HIGH

**DoRA vs LoRA:**
- DoRA: Dynamic rank allocation per layer
- Better accuracy, similar parameters
- Experimental but promising

**Implementation:**
```python
# backend/training/dora_trainer.py
from peft import get_peft_model, DoraConfig

def create_dora_model(base_model, config):
    dora_config = DoraConfig(
        r=config.rank,
        lora_alpha=config.alpha,
        target_modules=config.target_modules,
        lora_dropout=config.dropout,
        task_type="CAUSAL_LM",
        # DoRA-specific
        use_dora=True,
        init_dora_weights=True,
    )
    
    model = get_peft_model(base_model, dora_config)
    return model
```

---

#### Task 3.5: RLHF Pipeline
**Verantwortlich:** ML Engineer  
**Aufwand:** 2 Wochen  
**Priorität:** 🟢 MEDIUM

**RLHF Components:**
1. **Reward Model Training**
2. **PPO Training**
3. **Feedback Collection**

**Implementation:**
```python
# backend/training/rlhf/reward_model.py
class RewardModel(nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base = base_model
        self.value_head = nn.Linear(base_model.config.hidden_size, 1)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.base(input_ids, attention_mask=attention_mask)
        rewards = self.value_head(outputs.last_hidden_state[:, -1, :])
        return rewards

# backend/training/rlhf/ppo_trainer.py
class PPOTrainer:
    def __init__(self, policy_model, reward_model, config):
        self.policy = policy_model
        self.reward = reward_model
        self.config = config
    
    def train_step(self, prompts, responses):
        # 1. Get rewards
        rewards = self.reward(responses)
        
        # 2. Compute advantages
        advantages = self.compute_advantages(rewards)
        
        # 3. Update policy
        loss = self.ppo_loss(prompts, responses, advantages)
        loss.backward()
        self.optimizer.step()
```

---

## Phase 4: Enterprise & Ecosystem (Q2-Q4 2027)

### Sprint 25-28: Security Hardening (4 Wochen)

#### Task 4.1: Zero-Trust Architecture
**Verantwortlich:** Security Engineer + DevOps  
**Aufwand:** 2 Wochen  
**Priorität:** 🔴 CRITICAL

**Principles:**
1. Never trust, always verify
2. Least privilege access
3. Assume breach
4. Verify explicitly

**Implementation:**

**Service-to-Service Auth (Istio):**
```yaml
# templates/istio/authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: training-authz
spec:
  selector:
    matchLabels:
      app: training
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/vcc-clara/sa/frontend"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/training/*"]
    when:
    - key: request.auth.claims[role]
      values: ["admin", "trainer"]
```

**Network Policies:**
```yaml
# templates/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: training-network-policy
spec:
  podSelector:
    matchLabels:
      app: training
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 45680
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
```

---

#### Task 4.2: Secrets Management (Vault)
**Verantwortlich:** Security Engineer  
**Aufwand:** 1 Woche  
**Priorität:** 🔴 CRITICAL

**HashiCorp Vault Integration:**
```python
# shared/security/vault_client.py
import hvac

class VaultClient:
    def __init__(self, url: str, token: str):
        self.client = hvac.Client(url=url, token=token)
    
    def get_secret(self, path: str):
        """Retrieve secret from Vault"""
        secret = self.client.secrets.kv.v2.read_secret_version(path=path)
        return secret['data']['data']
    
    def get_database_credentials(self):
        """Get dynamic database credentials"""
        creds = self.client.secrets.database.generate_credentials(
            name='vcc-clara-postgres'
        )
        return creds['data']
    
    def renew_lease(self, lease_id: str):
        """Renew dynamic secret lease"""
        self.client.sys.renew_lease(lease_id=lease_id)
```

**Vault Agent Injector (Kubernetes):**
```yaml
# Pod annotation for secret injection
apiVersion: v1
kind: Pod
metadata:
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "vcc-clara-training"
    vault.hashicorp.com/agent-inject-secret-database: "database/creds/vcc-clara"
    vault.hashicorp.com/agent-inject-template-database: |
      {{- with secret "database/creds/vcc-clara" -}}
      export DATABASE_URL="postgresql://{{ .Data.username }}:{{ .Data.password }}@postgres:5432/clara"
      {{- end }}
spec:
  # ... pod spec
```

---

### Sprint 29-32: VCC Ecosystem Integration (4 Wochen)

#### Task 4.3: Shared Event Bus (Kafka)
**Verantwortlich:** Integration Engineer  
**Aufwand:** 1 Woche  
**Priorität:** 🔴 CRITICAL

**Kafka Topics:**
```
vcc.clara.training.started
vcc.clara.training.completed
vcc.clara.training.failed
vcc.clara.model.registered
vcc.clara.inference.requested
vcc.clara.inference.completed
vcc.veritas.document.processed
vcc.veritas.analysis.completed
```

**Event Schema (Avro):**
```json
{
  "type": "record",
  "name": "TrainingCompleted",
  "namespace": "org.vcc.clara.events",
  "fields": [
    {"name": "job_id", "type": "string"},
    {"name": "model_id", "type": "string"},
    {"name": "timestamp", "type": "long"},
    {"name": "metrics", "type": {
      "type": "record",
      "name": "Metrics",
      "fields": [
        {"name": "accuracy", "type": "double"},
        {"name": "loss", "type": "double"}
      ]
    }},
    {"name": "metadata", "type": {"type": "map", "values": "string"}}
  ]
}
```

**Producer:**
```python
# shared/events/kafka_producer.py
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

class EventProducer:
    def __init__(self, bootstrap_servers: str, schema_registry_url: str):
        self.producer = Producer({'bootstrap.servers': bootstrap_servers})
        self.schema_registry = SchemaRegistryClient({'url': schema_registry_url})
    
    def publish_training_completed(self, job_id: str, model_id: str, metrics: dict):
        event = {
            "job_id": job_id,
            "model_id": model_id,
            "timestamp": int(time.time() * 1000),
            "metrics": metrics,
            "metadata": {}
        }
        
        self.producer.produce(
            topic="vcc.clara.training.completed",
            value=avro_serializer(event),
            key=job_id
        )
        self.producer.flush()
```

---

#### Task 4.4: API Gateway Integration
**Verantwortlich:** Backend Engineer  
**Aufwand:** 3 Tage  
**Priorität:** 🟡 HIGH

**Kong/KrakenD Gateway:**
```yaml
# kong.yaml
services:
  - name: vcc-clara-training
    url: http://training.vcc-clara.svc.cluster.local:45680
    routes:
      - name: training-api
        paths:
          - /api/v1/training
        methods:
          - GET
          - POST
          - PUT
          - DELETE
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          hour: 1000
      - name: jwt
        config:
          secret_is_base64: false
          key_claim_name: iss
      - name: correlation-id
      - name: prometheus
```

---

## Acceptance Criteria & Definition of Done

### Phase 1 DoD
- [ ] Test Coverage >80%
- [ ] Documentation >95% complete
- [ ] CI/CD pipeline functional
- [ ] All endpoints have OpenAPI specs
- [ ] Security scan passes
- [ ] No P0/P1 bugs

### Phase 2 DoD
- [ ] All services run in Kubernetes
- [ ] Autoscaling configured and tested
- [ ] Managed database in use
- [ ] Service mesh operational
- [ ] Deployment time <5 minutes
- [ ] Uptime >99.9%

### Phase 3 DoD
- [ ] MLflow tracking all experiments
- [ ] Model registry operational
- [ ] DoRA/RLHF implemented and tested
- [ ] Feature store populated
- [ ] Model performance +15%
- [ ] Inference latency <100ms P95

### Phase 4 DoD
- [ ] Zero-Trust architecture verified
- [ ] Vault managing all secrets
- [ ] Multi-tenancy functional
- [ ] Kafka event bus operational
- [ ] VCC components integrated
- [ ] ISO 27001 compliant

---

## Timeline Summary

| Phase | Duration | Start | End | Dependencies |
|-------|----------|-------|-----|--------------|
| Phase 1 | 8 weeks | Q4 2025 | Q1 2026 | None |
| Phase 2 | 16 weeks | Q2 2026 | Q3 2026 | Phase 1 complete |
| Phase 3 | 16 weeks | Q4 2026 | Q1 2027 | Phase 2 complete |
| Phase 4 | 24 weeks | Q2 2027 | Q4 2027 | Phase 3 complete |

**Total Duration:** ~18 months (64 weeks)

---

## Resource Allocation

| Role | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|------|---------|---------|---------|---------|
| Tech Lead | 1 FTE | 1 FTE | 1 FTE | 1 FTE |
| Backend Dev | 1 FTE | 2 FTE | 2 FTE | 3 FTE |
| ML Engineer | 0.5 FTE | 1 FTE | 3 FTE | 2 FTE |
| DevOps | 0.5 FTE | 2 FTE | 1 FTE | 1 FTE |
| QA Engineer | 1 FTE | 1 FTE | 1 FTE | 1 FTE |
| Security | 0.5 FTE | 0.5 FTE | 0.5 FTE | 2 FTE |
| Tech Writer | 0.5 FTE | 0.5 FTE | 0.5 FTE | 1 FTE |

---

## Conclusion

This roadmap provides a detailed, actionable plan to transform VCC-Clara from its current state into a world-class, cloud-native AI platform. Each phase builds on the previous, ensuring controlled evolution while delivering continuous value.

**Next Steps:**
1. Review and approve roadmap
2. Allocate resources for Phase 1
3. Set up project tracking (Jira/GitHub Projects)
4. Begin Sprint 1

---

**Dokument-Status:** ✅ Ready for Implementation  
**Verantwortlich:** Technical Lead  
**Review:** Quarterly  
**Kontakt:** [tech-lead@vcc-project.org]

---

*Dieses Dokument wird zu Beginn jedes Sprints aktualisiert. Letzte Aktualisierung: 2025-11-23*
