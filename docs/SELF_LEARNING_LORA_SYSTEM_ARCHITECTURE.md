# Self-Learning LoRa/QLoRa System - Architecture & Implementation Plan

**Status:** ✅ **IMPLEMENTED** (See ARCHITECTURE.md for current production architecture)  
**Original Date:** 24. Oktober 2025  
**Implementation Completed:** November 2025  
**Original Goal:** FastAPI Backend + Frontend für selbstlernendes LoRa/QLoRa-System mit UDS3 Hybrid Search Integration

> **📌 Note:** This document described the original architecture plan. The system has been **fully implemented** and is now in **production**. For current architecture, see **[ARCHITECTURE.md](./ARCHITECTURE.md)**.

---

## 🎯 Projektübersicht

### Original Vision (Now Implemented ✅)
Ein produktionsreifes, selbstlernendes AI-System basierend auf LoRa/QLoRa-Adaptern, das:
- ✅ **Datensätze** über UDS3 Hybrid Search intelligent auswählt (IMPLEMENTED - optional)
- ✅ **Training** automatisiert und kontinuierlich durchführt (IMPLEMENTED)
- ✅ **Adapter** dynamisch verwaltet und intelligent routet (IMPLEMENTED)
- ✅ **Skaliert** von Ollama (Development) zu vLLM Multi-LoRa (Production) (IMPLEMENTED)

### Implementation Status (November 2025)
- ✅ **Kontinuierliches Lernen:** Implemented in `backend/continuous_learning/`
- ✅ **Training Backend:** Microservice on Port 45680
- ✅ **Dataset Backend:** Microservice on Port 45681
- ✅ **Frontend Applications:** Admin, Training, Data Preparation (3 tkinter GUIs)
- ✅ **UDS3 Integration:** Optional hybrid search (graceful degradation)
- ✅ **Configuration System:** Pydantic-based centralized config
- ✅ **Security Framework:** JWT authentication with 4 security modes

**For current architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md)**

---

## 🏗️ System-Architektur

### Implementation Status

**This section described the planned architecture. Current production architecture:**
- **Training Backend:** Port 45680 (FastAPI) ✅ IMPLEMENTED
- **Dataset Backend:** Port 45681 (FastAPI) ✅ IMPLEMENTED
- **Frontend Layer:** 3 tkinter applications ✅ IMPLEMENTED
- **Database Layer:** PostgreSQL + optional UDS3 ✅ IMPLEMENTED
- **Security Layer:** JWT + RBAC ✅ IMPLEMENTED

**See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed current architecture.**

### Microservices-Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Dataset    │  │   Training   │  │   Adapter    │  │   Login    │ │
│  │   Explorer   │  │   Monitor    │  │   Manager    │  │   (SSO)    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                    WebSocket + REST API + JWT
                              │
┌─────────────────────────────────────────────────────────────────────────┐
│                        Security Layer (VCC)                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────────┐│
│  │  Veritas Edge    │  │  User Service    │  │  PKI Service          ││
│  │  Port: 5000      │  │  Port: 5001      │  │  Port: 8443           ││
│  │  • API Gateway   │  │  • JWT Auth      │  │  • CA Management      ││
│  │  • OIDC/SSO      │  │  • RBAC          │  │  • mTLS Certs         ││
│  │  • Routing       │  │  • AD Integration│  │  • Auto-Renewal       ││
│  └──────────────────┘  └──────────────────┘  └───────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                              │ JWT Token Propagation
                              ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      Backend Services (CLARA)                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐        │
│  │  Main Backend    │  │  Ingestion       │  │  Training     │        │
│  │  Port: 45678     │  │  Port: 45679     │  │  Port: 45680  │        │
│  │  • Queries       │  │  • Doc Upload    │  │  • Job Mgmt   │        │
│  │  • DSGVO         │  │  • Processing    │  │  • LoRa Train │        │
│  │  • Review Queue  │  │  • UDS3 Write    │  │  • Eval       │        │
│  │  🔐 JWT Required │  │  🔐 JWT Required │  │  🔐 JWT Req.  │        │
│  └──────────────────┘  └──────────────────┘  └───────────────┘        │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐        │
│  │  Dataset Mgmt    │  │  Model Serving   │  │  Metrics      │        │
│  │  Port: 45681     │  │  Port: 45682     │  │  Port: 9310   │        │
│  │  • UDS3 Search   │  │  • vLLM Engine   │  │  • Prometheus │        │
│  │  • Quality Check │  │  • Multi-LoRa    │  │  • Grafana    │        │
│  │  • Export        │  │  • Router        │  │  • Alerts     │        │
│  │  🔐 JWT Required │  │  🔐 JWT Required │  │  🔓 Public    │        │
│  └──────────────────┘  └──────────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                    Database Layer (UDS3)
                              │
┌─────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  PostgreSQL  │  │  ChromaDB    │  │  Neo4j       │  │  Keycloak  │ │
│  │  Port: 5432  │  │  Port: 8000  │  │  Port: 7687  │  │  Port:8080 │ │
│  │  • Metadata  │  │  • Vectors   │  │  • Graph     │  │  • OIDC    │ │
│  │  • Jobs      │  │  • Embeddings│  │  • Relations │  │  • AD Sync │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Komponenten-Details

### 0. Security & Identity Layer (VCC Integration) 🆕

**VCC User Service** & **Veritas Edge** stellen Enterprise-Security für alle CLARA Services bereit.

#### Veritas Edge Service (API Gateway)
- **Port:** 5000
- **Technologie:** ASP.NET Core + YARP
- **Verantwortlichkeiten:**
  - Single Entry Point für alle CLARA Services
  - OIDC/Keycloak Authentication
  - JWT Token Issuance & Validation
  - Service Routing & Load Balancing
  - Rate Limiting & DDoS Protection

**Konfiguration:**
```yaml
# veritas-config.yaml
routes:
  - path: "/api/training/**"
    backend: "http://localhost:45680"
    auth_required: true
    roles: ["admin", "trainer"]
  
  - path: "/api/datasets/**"
    backend: "http://localhost:45681"
    auth_required: true
    roles: ["admin", "trainer", "analyst"]
  
  - path: "/api/serving/**"
    backend: "http://localhost:45682"
    auth_required: true
    roles: ["user"]

auth:
  oidc_authority: "http://localhost:8080/realms/vcc"
  client_id: "clara-training-system"
  client_secret: "${OIDC_CLIENT_SECRET}"
```

#### User Service (Identity & RBAC)
- **Port:** 5001
- **Technologie:** ASP.NET Core
- **Verantwortlichkeiten:**
  - User Management (CRUD)
  - Active Directory Integration
  - Role-Based Access Control (RBAC)
  - JWT Claims Management
  - User Profile Service

**Rollen-Modell:**
```python
class UserRole(Enum):
    """User Roles für CLARA Training System"""
    ADMIN = "admin"           # Volle Rechte (Training, Config, User Mgmt)
    TRAINER = "trainer"       # Training Jobs, Dataset Management
    ANALYST = "analyst"       # Dataset Search, Read-Only Training
    USER = "user"            # Inference/Serving nur
    AUDITOR = "auditor"      # Read-Only, Audit Logs

# Permissions Mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: ["*"],  # Alle Permissions
    UserRole.TRAINER: [
        "training:create", "training:read", "training:cancel",
        "datasets:create", "datasets:read", "datasets:export",
        "adapters:activate", "adapters:read"
    ],
    UserRole.ANALYST: [
        "datasets:read", "datasets:search",
        "training:read", "adapters:read"
    ],
    UserRole.USER: [
        "serving:generate", "adapters:read"
    ],
    UserRole.AUDITOR: [
        "training:read", "datasets:read", "adapters:read",
        "audit:read", "metrics:read"
    ]
}
```

#### PKI Service (Certificate Authority) 🆕
- **Port:** 8443
- **Technologie:** Python FastAPI
- **Verantwortlichkeiten:**
  - Service Certificate Issuance
  - mTLS for Service-to-Service Communication
  - Auto-Renewal (Background Thread)
  - Certificate Revocation List (CRL)
  - Audit Logging

**Integration:**
```python
# scripts/clara_training_backend.py

from vcc_pki_client import PKIClient

# PKI Integration für mTLS
pki_client = PKIClient(
    pki_server_url="https://localhost:8443",
    service_id="clara-training-backend"
)

# Certificate anfordern (einmalig)
pki_client.request_certificate(
    common_name="training.clara.local",
    san_dns=["training.clara.local", "localhost"],
    san_ip=["127.0.0.1"]
)

# Auto-Renewal aktivieren (läuft im Hintergrund)
pki_client.enable_auto_renewal()

# SSL Context für uvicorn
ssl_context = pki_client.get_ssl_context()

# FastAPI mit mTLS starten
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=SERVICE_PORT,
        ssl_context=ssl_context,  # mTLS enabled
        log_level="info"
    )
```

**PKI Features:**
- ✅ Root + Intermediate CA Hierarchy
- ✅ 5-Minute Integration (Zero Manual Work)
- ✅ Auto-Renewal (Background Thread)
- ✅ Service Discovery (via PostgreSQL)
- ✅ Audit Logging (alle Cert-Operationen)
- ✅ Admin CLI (15 Commands)

---

### 1. Training Backend Service (Port 45680)

**Verantwortlichkeiten:**
- LoRa/QLoRa Training orchestrieren
- Job-Queue Management
- Model Checkpointing
- Continuous Learning Pipeline

**OOP-Struktur:**
```python
class AdapterTrainingService(ABC):
    """Basis-Klasse für Adapter-Training (Template Method Pattern)"""
    
    @abstractmethod
    def prepare_dataset(self, config: TrainingConfig) -> Dataset:
        pass
    
    @abstractmethod
    def train(self, dataset: Dataset) -> TrainingResult:
        pass
    
    @abstractmethod
    def evaluate(self, model: PeftModel) -> EvaluationMetrics:
        pass
    
    @abstractmethod
    def save_adapter(self, model: PeftModel, path: Path) -> AdapterMetadata:
        pass

class LoRATrainer(AdapterTrainingService):
    """Standard LoRa Training (Full Precision)"""
    # Implementierung basierend auf clara_train_lora.py

class QLoRATrainer(AdapterTrainingService):
    """Quantized LoRa Training (4-bit/8-bit)"""
    # Implementierung basierend auf clara_train_qlora.py

class ContinuousLoRATrainer(LoRATrainer):
    """Kontinuierliches Lernen mit Live-Buffer"""
    # Erweitert clara_continuous_learning.py
    
    buffer: LiveLearningBuffer
    dataset_manager: DatasetManager
    
    def integrate_feedback(self, feedback: UserFeedback) -> bool:
        """Feedback → Buffer → Auto-Training Pipeline"""
        pass
    
    def trigger_training_cycle(self) -> TrainingJob:
        """Automatisches Training bei Threshold-Erreichung"""
        pass
```

**API Endpoints:**
```python
POST   /api/training/jobs                 # Neuen Training Job erstellen
GET    /api/training/jobs/{job_id}        # Job-Status abrufen
GET    /api/training/jobs/list            # Alle Jobs auflisten
DELETE /api/training/jobs/{job_id}        # Job abbrechen
POST   /api/training/jobs/{job_id}/retry  # Job neu starten

WS     /ws/training                        # WebSocket für Live-Updates

# Security: JWT Required, Roles: admin, trainer
```

**JWT Middleware Integration:**
```python
# scripts/clara_training_backend.py

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from typing import Optional

security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "RS256"  # Keycloak verwendet RS256
JWT_ISSUER = "http://localhost:8080/realms/vcc"

async def verify_jwt_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Verifiziert JWT Token und extrahiert User Claims
    
    Returns:
        dict: User Claims (sub, email, roles, permissions)
    """
    token = credentials.credentials
    
    try:
        # Token validieren (RS256 mit Keycloak Public Key)
        payload = jwt.decode(
            token,
            key=get_keycloak_public_key(),
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
            audience="clara-training-system"
        )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_role(
    required_roles: List[str],
    user_claims: dict = Depends(verify_jwt_token)
) -> dict:
    """
    Prüft ob User benötigte Rolle hat
    
    Args:
        required_roles: Liste erlaubter Rollen (z.B. ["admin", "trainer"])
        user_claims: User Claims aus JWT Token
    
    Raises:
        HTTPException: 403 wenn Rolle nicht vorhanden
    
    Returns:
        dict: User Claims
    """
    user_roles = user_claims.get("realm_access", {}).get("roles", [])
    
    if not any(role in user_roles for role in required_roles):
        raise HTTPException(
            status_code=403,
            detail=f"Required roles: {required_roles}. User has: {user_roles}"
        )
    
    return user_claims

# Protected Endpoint
@app.post("/api/training/jobs", response_model=TrainingJobResponse)
async def create_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks,
    user_claims: dict = Depends(lambda: require_role(["admin", "trainer"]))
):
    """
    Erstellt neuen Training Job (Protected: admin, trainer)
    """
    # User aus JWT Token
    user_id = user_claims.get("sub")
    user_email = user_claims.get("email")
    
    logger.info(f"Training Job requested by: {user_email} ({user_id})")
    
    # Job erstellen mit User-Audit
    job = job_manager.create_job(request, created_by=user_id)
    
    # Audit Log
    audit_log.log_event(
        event_type="training_job_created",
        user_id=user_id,
        job_id=job.job_id,
        details={"config": request.config_path}
    )
    
    # ... rest of implementation
```

**Keycloak Public Key Fetching:**
```python
import requests
from functools import lru_cache

@lru_cache(maxsize=1)
def get_keycloak_public_key() -> str:
    """
    Holt Keycloak Public Key für JWT Validation
    
    Cache: 1 Stunde (Token-Signatur ändert sich selten)
    """
    jwks_url = f"{JWT_ISSUER}/protocol/openid-connect/certs"
    
    response = requests.get(jwks_url)
    response.raise_for_status()
    
    jwks = response.json()
    
    # Extrahiere ersten Key (RS256)
    for key in jwks["keys"]:
        if key["alg"] == "RS256" and key["use"] == "sig":
            # Konvertiere zu PEM Format
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from jose import jwk
            
            public_key = jwk.construct(key).public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode()
    
    raise ValueError("No suitable RS256 key found in JWKS")
```

**Konfiguration:**
```yaml
# configs/training_backend_config.yaml
service:
  name: "clara_training_backend"
  port: 45680
  workers: 4

training:
  max_concurrent_jobs: 2          # GPU-Limitierung
  job_timeout_minutes: 120
  checkpoint_interval_steps: 500
  auto_cleanup_days: 30

continuous_learning:
  enabled: true
  buffer_size: 500
  quality_threshold: 0.0
  train_interval_seconds: 300     # 5 Minuten
  min_batch_size: 50

gpu:
  device_map: "auto"
  gradient_checkpointing: true
  fp16: true
  max_memory: "10GB"
```

---

### 2. Dataset Management Service (Port 45681)

**Verantwortlichkeiten:**
- UDS3 Hybrid Search Integration
- Dataset-Qualitätsprüfung
- Training-Data Export
- Dataset-Registry Verwaltung

**OOP-Struktur:**
```python
class DatasetManager:
    """Zentrale Dataset-Verwaltung mit UDS3 Integration"""
    
    def __init__(self, uds3_strategy: UnifiedDatabaseStrategy):
        self.search_api = UDS3SearchAPI(uds3_strategy)
        self.quality_checker = DatasetQualityChecker()
        self.registry = DatasetRegistry()
    
    async def search_datasets(
        self, 
        query: SearchQuery,
        filters: Optional[DatasetFilters] = None
    ) -> List[SearchResult]:
        """Hybrid Search über UDS3"""
        return await self.search_api.hybrid_search(query)
    
    def prepare_training_data(
        self, 
        results: List[SearchResult],
        config: PreprocessingConfig
    ) -> TrainingDataset:
        """SearchResults → Training-Dataset Konvertierung"""
        # Deduplizierung, Tokenisierung, Quality-Filter
        pass
    
    def export_dataset(
        self, 
        dataset_id: str, 
        format: ExportFormat
    ) -> Path:
        """Export als JSONL/Parquet für Training"""
        pass

class DatasetQualityChecker:
    """Automatische Qualitätsprüfung"""
    
    def analyze(self, text: str) -> QualityScore:
        """
        Checks:
        - Länge (min/max)
        - Encoding (UTF-8 Validität)
        - Duplikate (Hashing)
        - Toxizität (Content-Filter)
        - Domain-Relevanz (UDS3 Graph)
        """
        pass

class DatasetRegistry:
    """PostgreSQL-basierte Dataset-Verwaltung"""
    
    def register_dataset(self, metadata: DatasetMetadata) -> str:
        pass
    
    def get_dataset(self, dataset_id: str) -> Dataset:
        pass
    
    def list_datasets(self, filters: Dict) -> List[DatasetMetadata]:
        pass
```

**API Endpoints:**
```python
POST   /api/datasets/search               # UDS3 Hybrid Search
GET    /api/datasets/{dataset_id}         # Dataset-Details
POST   /api/datasets/create               # Neues Dataset erstellen
POST   /api/datasets/{id}/analyze         # Quality-Analyse
POST   /api/datasets/{id}/export          # Export (JSONL/Parquet)
GET    /api/datasets/list                 # Alle Datasets

# UDS3 Integration
POST   /api/datasets/search/vector        # Semantic Vector Search
POST   /api/datasets/search/graph         # Graph-basierte Suche
POST   /api/datasets/search/hybrid        # Kombinierte Suche
```

**UDS3 Hybrid Search Integration:**
```python
# Example: Dataset-Auswahl über Hybrid Search
from uds3.search.search_api import UDS3SearchAPI, SearchQuery

search_query = SearchQuery(
    query_text="Verwaltungsrecht Photovoltaik Genehmigung",
    top_k=100,
    search_types=["vector", "graph", "keyword"],
    weights={"vector": 0.5, "graph": 0.3, "keyword": 0.2},
    filters={"document_type": "regulation", "min_quality": 0.7}
)

results = await dataset_manager.search_datasets(search_query)

# Quality-Filter anwenden
filtered_results = [
    r for r in results 
    if r.metadata.get('quality_score', 0) >= 0.7
    and len(r.content) >= 100
]

# Training-Dataset erstellen
training_dataset = dataset_manager.prepare_training_data(
    filtered_results,
    config=PreprocessingConfig(
        max_length=512,
        remove_duplicates=True,
        augmentation=False
    )
)
```

---

### 3. Model Serving Service (Port 45682)

**Verantwortlichkeiten:**
- vLLM-basiertes Multi-LoRa Serving
- Adapter Hot-Swap zur Laufzeit
- Intelligentes Routing (AdapterRouter)
- Load Balancing zwischen Adaptern

**OOP-Struktur:**
```python
class MultiLoRAServingEngine:
    """vLLM-basiertes Multi-LoRa Serving"""
    
    def __init__(self, base_model: str):
        if VLLM_AVAILABLE:
            self.engine = LLM(model=base_model)
        else:
            # Ollama Fallback für Development
            self.engine = OllamaEngine(base_model)
        
        self.adapters: Dict[str, LoRAAdapter] = {}
        self.router = AdapterRouter()
    
    def load_adapter(self, adapter_path: Path) -> str:
        """Lädt LoRa Adapter zur Laufzeit"""
        adapter_id = self._register_adapter(adapter_path)
        
        if VLLM_AVAILABLE:
            self.engine.add_lora(adapter_id, adapter_path)
        
        return adapter_id
    
    def activate_adapter(self, adapter_id: str) -> bool:
        """Aktiviert spezifischen Adapter"""
        if adapter_id not in self.adapters:
            raise ValueError(f"Adapter {adapter_id} not loaded")
        
        self.adapters[adapter_id].active = True
        return True
    
    async def generate(
        self, 
        prompt: str,
        route: bool = True,
        adapter_id: Optional[str] = None
    ) -> GenerationResult:
        """Text-Generierung mit optionalem Routing"""
        
        # Intelligentes Routing
        if route and adapter_id is None:
            routing_result = self.router.route(prompt)
            adapter_id = routing_result.adapter_id
        
        # Generierung
        if VLLM_AVAILABLE:
            lora_request = LoRARequest(adapter_id, ...)
            output = self.engine.generate(prompt, lora_request=lora_request)
        else:
            # Ollama Fallback
            output = await self.engine.generate(prompt)
        
        return GenerationResult(
            text=output,
            adapter_id=adapter_id,
            routing_confidence=routing_result.confidence
        )
```

**API Endpoints:**
```python
POST   /api/serving/load_adapter          # Adapter laden
POST   /api/serving/activate_adapter      # Adapter aktivieren
DELETE /api/serving/unload_adapter        # Adapter entladen
GET    /api/serving/adapters/list         # Alle geladenen Adapter

POST   /api/serving/generate              # Text-Generierung
POST   /api/serving/generate/stream       # Streaming-Generierung
POST   /api/serving/generate/batch        # Batch-Generierung

GET    /api/serving/router/status         # Router-Status
POST   /api/serving/router/configure      # Router-Konfiguration
```

**Migration: Ollama → vLLM**
```python
# Development (Ollama)
CLARA_SERVING_ENGINE=ollama python -m scripts.clara_serve_vllm

# Production (vLLM)
CLARA_SERVING_ENGINE=vllm python -m scripts.clara_serve_vllm
```

---

### 4. Continuous Learning Pipeline

**Workflow:**
```
User Interaction → Feedback Collection → Quality Filter → Learning Buffer
                                                               │
                                                               ↓
                                                      Threshold Check
                                                               │
                                      ┌────────────────────────┴────────────────────┐
                                      ↓                                             ↓
                              Zeit-Trigger (5 min)                          Size-Trigger (50 Samples)
                                      │                                             │
                                      └──────────────────┬──────────────────────────┘
                                                         ↓
                                            Trigger Training Job
                                                         │
                                                         ↓
                              ┌──────────────────────────────────────────┐
                              │  Dataset Preparation                      │
                              │  • UDS3 Hybrid Search Integration        │
                              │  • Quality-Filter                        │
                              │  • Deduplizierung                        │
                              └──────────────────────────────────────────┘
                                                         │
                                                         ↓
                              ┌──────────────────────────────────────────┐
                              │  LoRa Training                           │
                              │  • Incremental Learning                  │
                              │  • Low Learning Rate (5e-6)              │
                              │  • Single Epoch                          │
                              └──────────────────────────────────────────┘
                                                         │
                                                         ↓
                              ┌──────────────────────────────────────────┐
                              │  Evaluation                              │
                              │  • Perplexity auf Validation Set         │
                              │  • Regression Test                       │
                              │  • Domain-Specific Metrics               │
                              └──────────────────────────────────────────┘
                                                         │
                                  ┌─────────────────────┴─────────────────────┐
                                  ↓                                           ↓
                          Metrics OK?                                  Metrics Bad?
                                  │                                           │
                                  ↓                                           ↓
                       Save & Register Adapter                      Rollback to Previous
                                  │                                           │
                                  ↓                                           ↓
                       Auto-Activate in Router                      Log Failure Event
```

**Implementierung:**
```python
class ContinuousLearningPipeline:
    """Orchestriert kontinuierliches Lernen"""
    
    def __init__(self, config: ContinuousLearningConfig):
        self.trainer = ContinuousLoRATrainer(config)
        self.dataset_manager = DatasetManager(uds3_strategy)
        self.evaluator = AdapterEvaluator()
        self.router = AdapterRouter()
        
        self.buffer = LiveLearningBuffer(
            max_size=config.buffer_size,
            quality_threshold=config.quality_threshold
        )
    
    async def add_feedback(self, feedback: UserFeedback) -> bool:
        """Fügt User-Feedback zum Buffer hinzu"""
        
        # Quality-Check
        quality_score = self._calculate_quality(feedback)
        if quality_score < self.config.quality_threshold:
            return False
        
        # Buffer hinzufügen
        sample = LiveSample(
            text=feedback.text,
            feedback_score=feedback.rating,
            importance=feedback.importance,
            source="user_feedback"
        )
        
        added = self.buffer.add_sample(sample)
        
        # Check Trigger-Bedingungen
        if self._should_trigger_training():
            await self.trigger_training_cycle()
        
        return added
    
    async def trigger_training_cycle(self) -> TrainingJob:
        """Startet automatischen Training-Zyklus"""
        
        # 1. Batch aus Buffer holen
        batch = self.buffer.get_quality_batch(
            batch_size=self.config.min_batch_size
        )
        
        # 2. Optional: Zusätzliche Daten via UDS3 Hybrid Search
        if self.config.augment_with_search:
            search_results = await self._search_related_data(batch)
            batch.extend(search_results)
        
        # 3. Training-Dataset erstellen
        dataset = self.dataset_manager.prepare_training_data(
            batch, 
            config=self.config.preprocessing
        )
        
        # 4. Training starten (Background Job)
        job = await self.trainer.train_async(dataset)
        
        # 5. Nach Training: Evaluation
        if job.status == JobStatus.COMPLETED:
            metrics = await self.evaluator.evaluate(job.adapter_path)
            
            # 6. Quality Gate Check
            if metrics.passes_quality_gate():
                # Erfolg: Adapter registrieren & aktivieren
                adapter_id = self.router.register_adapter(
                    job.adapter_path,
                    metrics=metrics
                )
                self.router.activate_adapter(adapter_id)
            else:
                # Fehler: Rollback
                logger.warning(f"Adapter failed quality gate: {metrics}")
                self._rollback_to_previous()
        
        return job
    
    def _should_trigger_training(self) -> bool:
        """Prüft ob Training getriggert werden soll"""
        
        # Zeit-basierter Trigger
        time_since_last = (datetime.now() - self.last_training).seconds
        if time_since_last >= self.config.train_interval_seconds:
            return True
        
        # Size-basierter Trigger
        buffer_size = self.buffer.get_stats()['count']
        if buffer_size >= self.config.trigger_threshold:
            return True
        
        return False
    
    async def _search_related_data(
        self, 
        batch: List[LiveSample]
    ) -> List[LiveSample]:
        """Sucht verwandte Daten via UDS3 für Augmentation"""
        
        # Extrahiere Keywords aus Batch
        keywords = self._extract_keywords(batch)
        
        # UDS3 Hybrid Search
        search_query = SearchQuery(
            query_text=" ".join(keywords),
            top_k=20,
            search_types=["vector", "graph"],
            weights={"vector": 0.6, "graph": 0.4}
        )
        
        results = await self.dataset_manager.search_datasets(search_query)
        
        # Konvertiere zu LiveSamples
        augmented_samples = [
            LiveSample(
                text=r.content,
                feedback_score=0.5,  # Neutral
                importance=2,
                source="uds3_augmentation"
            )
            for r in results
        ]
        
        return augmented_samples
```

---

## 🎨 Frontend Werkzeugkasten

### Seiten-Struktur

**1. Dataset Explorer**
```python
class DatasetExplorerView:
    """UDS3 Hybrid Search UI"""
    
    components = [
        SearchBar(placeholder="Verwaltungsrecht Photovoltaik..."),
        FilterPanel(
            filters=[
                DocumentTypeFilter(),
                DomainFilter(),
                DateRangeFilter(),
                QualityScoreFilter()
            ]
        ),
        SearchTypeSelector(
            options=["Vector", "Graph", "Keyword", "Hybrid"]
        ),
        WeightSliders(
            vector_weight=0.5,
            graph_weight=0.3,
            keyword_weight=0.2
        ),
        ResultsTable(
            columns=["Preview", "Score", "Source", "Quality", "Actions"]
        ),
        PreviewPanel(),
        ExportButton(formats=["JSONL", "Parquet", "CSV"])
    ]
```

**2. Training Monitor**
```python
class TrainingMonitorView:
    """Live Training-Überwachung"""
    
    components = [
        JobStatusTable(
            columns=["Job ID", "Status", "Progress", "ETA", "Metrics"]
        ),
        LiveMetricsChart(
            metrics=["Loss", "Perplexity", "Learning Rate"]
        ),
        LogViewer(
            websocket_url="/ws/training",
            auto_scroll=True
        ),
        ActionButtons([
            "Start New Job",
            "Pause",
            "Stop",
            "Retry Failed"
        ])
    ]
```

**3. Adapter Manager**
```python
class AdapterManagerView:
    """Adapter-Registry Management"""
    
    components = [
        AdapterTable(
            columns=[
                "ID", "Version", "Domain", "Status", 
                "Metrics", "Created", "Actions"
            ]
        ),
        AdapterDetails(
            fields=[
                "domain_score", "ppl_dev", "user_feedback",
                "training_samples", "base_model"
            ]
        ),
        ActivationControl(),
        VersionComparison(),
        PerformanceChart()
    ]
```

**WebSocket Integration:**
```python
class TrainingWebSocketClient:
    """Real-Time Training Updates (analog zu IngestionWebSocketClient)"""
    
    def __init__(self, ws_url: str = "ws://localhost:45680/ws/training"):
        self.ws = None
        self.callbacks = {}
        self.reconnect_delay = 5
    
    async def connect(self):
        """Verbindet zum Training WebSocket"""
        self.ws = await websockets.connect(self.ws_url)
        asyncio.create_task(self._message_handler())
    
    async def _message_handler(self):
        """Verarbeitet eingehende Messages"""
        async for message in self.ws:
            data = json.loads(message)
            event_type = data.get("type")
            
            if event_type in self.callbacks:
                self.callbacks[event_type](data)
    
    def on_job_update(self, callback: Callable):
        """Registriert Callback für Job-Updates"""
        self.callbacks["job_update"] = callback
    
    def on_metrics_update(self, callback: Callable):
        """Registriert Callback für Metrics"""
        self.callbacks["metrics_update"] = callback
```

---

## ⚙️ Konfigurationsmanagement

### Zentrale Config-Struktur
```yaml
# configs/system_config.yaml
system:
  name: "CLARA Self-Learning LoRa System"
  environment: "development"  # development, staging, production
  
services:
  main_backend:
    enabled: true
    port: 45678
  
  ingestion_backend:
    enabled: true
    port: 45679
  
  training_backend:
    enabled: true
    port: 45680
    max_concurrent_jobs: 2
  
  dataset_management:
    enabled: true
    port: 45681
  
  model_serving:
    enabled: true
    port: 45682
    engine: "ollama"  # ollama, vllm

uds3:
  postgresql:
    host: "192.168.178.94"
    port: 5432
    database: "postgres"
  
  chromadb:
    host: "192.168.178.94"
    port: 8000
  
  neo4j:
    host: "192.168.178.94"
    port: 7687

training:
  default_trainer: "qlora"  # lora, qlora
  
  lora:
    r: 16
    alpha: 32
    dropout: 0.1
    target_modules:
      - "q_proj"
      - "v_proj"
      - "k_proj"
      - "o_proj"
  
  qlora:
    r: 16
    alpha: 32
    dropout: 0.1
    bits: 4  # 4-bit Quantisierung

continuous_learning:
  enabled: true
  buffer_size: 500
  quality_threshold: 0.0
  train_interval_seconds: 300
  min_batch_size: 50
  augment_with_search: true

dataset:
  default_search_type: "hybrid"
  search_weights:
    vector: 0.5
    graph: 0.3
    keyword: 0.2
  
  quality:
    min_length: 50
    max_length: 2048
    min_quality_score: 0.5
    check_toxicity: true

router:
  default_adapter: "base_default_adapter"
  enable_embeddings: false
  enable_exploration: false
  thresholds:
    hard_domain: 1.5
    conf_low: 0.55
    conf_high: 0.85

metrics:
  prometheus_enabled: true
  prometheus_port: 9310
  grafana_enabled: false

security:
  jwt_enabled: false  # Production: true
  rate_limiting: false  # Production: true
  https_only: false  # Production: true
```

### Pydantic Config Models
```python
from pydantic import BaseSettings, Field

class ServiceConfig(BaseSettings):
    name: str
    port: int
    workers: int = 4
    
    class Config:
        env_prefix = "CLARA_SERVICE_"

class UDS3Config(BaseSettings):
    postgresql_host: str = Field(..., env="UDS3_POSTGRES_HOST")
    postgresql_port: int = Field(5432, env="UDS3_POSTGRES_PORT")
    chromadb_host: str = Field(..., env="UDS3_CHROMA_HOST")
    neo4j_host: str = Field(..., env="UDS3_NEO4J_HOST")

class TrainingConfig(BaseSettings):
    default_trainer: str = "qlora"
    max_concurrent_jobs: int = 2
    
    class Config:
        env_prefix = "CLARA_TRAINING_"

class SystemConfig(BaseSettings):
    """Zentrale System-Konfiguration"""
    
    service: ServiceConfig
    uds3: UDS3Config
    training: TrainingConfig
    
    @classmethod
    def from_yaml(cls, config_path: Path) -> "SystemConfig":
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return cls(**data)
```

---

## 🔒 Security & Best Practices

### 1. JWT-basierte Authentifizierung (VCC Integration) 🆕

**Flow:**
```
User → Browser → Veritas Edge (Port 5000)
                    ↓ OIDC Login
                 Keycloak (Port 8080)
                    ↓ JWT Token
             Frontend with JWT
                    ↓ API Calls with Authorization: Bearer <JWT>
         Training Backend (Port 45680) → verify_jwt_token()
                    ↓ Success
              Process Request
```

**JWT Token Structure:**
```json
{
  "sub": "user-uuid-1234",
  "email": "trainer@vcc.local",
  "preferred_username": "trainer",
  "realm_access": {
    "roles": ["trainer", "analyst"]
  },
  "resource_access": {
    "clara-training-system": {
      "roles": ["training:create", "datasets:read"]
    }
  },
  "iss": "http://localhost:8080/realms/vcc",
  "aud": "clara-training-system",
  "exp": 1729784400,
  "iat": 1729780800
}
```

**Backend JWT Middleware:**
```python
# shared/jwt_middleware.py (analog zu VCC User Service)

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
import jwt
import requests
from functools import lru_cache
from typing import Optional, List

class JWTMiddleware:
    """JWT Middleware für CLARA Services"""
    
    def __init__(
        self,
        keycloak_url: str = "http://localhost:8080",
        realm: str = "vcc",
        client_id: str = "clara-training-system"
    ):
        self.keycloak_url = keycloak_url
        self.realm = realm
        self.client_id = client_id
        self.issuer = f"{keycloak_url}/realms/{realm}"
        self._public_key_cache = None
    
    @lru_cache(maxsize=1)
    def get_public_key(self) -> str:
        """Fetch Keycloak Public Key (cached 1h)"""
        jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
        response = requests.get(jwks_url, timeout=5)
        response.raise_for_status()
        
        jwks = response.json()
        for key in jwks["keys"]:
            if key["alg"] == "RS256":
                return self._jwk_to_pem(key)
        
        raise ValueError("No RS256 key found")
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT Token"""
        try:
            public_key = self.get_public_key()
            
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                issuer=self.issuer,
                audience=self.client_id,
                options={"verify_exp": True}
            )
            
            return payload
        
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    
    def require_roles(self, required_roles: List[str]):
        """Decorator for role-based access control"""
        async def dependency(request: Request):
            # Extract token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing JWT token")
            
            token = auth_header[7:]  # Remove "Bearer "
            
            # Verify token
            claims = self.verify_token(token)
            
            # Check roles
            user_roles = claims.get("realm_access", {}).get("roles", [])
            
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Required roles: {required_roles}"
                )
            
            # Attach claims to request state
            request.state.user = claims
            
            return claims
        
        return dependency
    
    @staticmethod
    def _jwk_to_pem(jwk: dict) -> str:
        """Convert JWK to PEM format"""
        from jose import jwk as jose_jwk
        from cryptography.hazmat.primitives import serialization
        
        public_key = jose_jwk.construct(jwk).public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode()

# Global Middleware Instance
jwt_middleware = JWTMiddleware()
```

**Usage in FastAPI:**
```python
from shared.jwt_middleware import jwt_middleware
from fastapi import Depends

# Protect endpoint
@app.post("/api/training/jobs")
async def create_training_job(
    request: TrainingJobRequest,
    user_claims: dict = Depends(jwt_middleware.require_roles(["admin", "trainer"]))
):
    user_id = user_claims["sub"]
    user_email = user_claims["email"]
    
    logger.info(f"Job created by: {user_email}")
    
    # ... implementation
```

### 2. mTLS for Service-to-Service (PKI Integration) 🆕

**Scenario:** Training Backend → Dataset Backend Communication

**Client Side (Training Backend):**
```python
from vcc_pki_client import PKIClient
import httpx

# PKI Client Setup
pki = PKIClient(
    pki_server_url="https://localhost:8443",
    service_id="clara-training-backend"
)

# Get SSL Context (mTLS Client Cert)
ssl_context = pki.get_ssl_context()

# HTTP Client with mTLS
async def call_dataset_service(query: str):
    """Call Dataset Service with mTLS"""
    async with httpx.AsyncClient(verify=ssl_context) as client:
        response = await client.post(
            "https://dataset.clara.local:45681/api/datasets/search",
            json={"query": query},
            headers={
                "Authorization": f"Bearer {get_current_jwt_token()}",  # JWT + mTLS
                "X-Service-ID": "clara-training-backend"
            }
        )
        return response.json()
```

**Server Side (Dataset Backend):**
```python
from vcc_pki_client import PKIClient
import uvicorn

# PKI Setup
pki = PKIClient(
    pki_server_url="https://localhost:8443",
    service_id="clara-dataset-backend"
)

# Request Certificate
pki.request_certificate(
    common_name="dataset.clara.local",
    san_dns=["dataset.clara.local", "localhost"]
)

# Auto-Renewal
pki.enable_auto_renewal()

# Start with mTLS
if __name__ == "__main__":
    ssl_context = pki.get_ssl_context()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=45681,
        ssl_context=ssl_context,  # mTLS Server
        ssl_ca_certs=pki.get_ca_bundle_path()  # Verify Client Certs
    )
```

**Benefits:**
- ✅ **Mutual Authentication:** Both sides verify each other
- ✅ **Zero-Trust:** No implicit trust between services
- ✅ **Auto-Renewal:** No manual certificate management
- ✅ **Audit Trail:** All mTLS connections logged

### 3. Authentifizierung (Production)
```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.post("/api/training/jobs")
async def create_training_job(
    request: TrainingJobRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # JWT Token validieren
    user = verify_jwt_token(credentials.credentials)
    
    # RBAC Check
    if user.role not in ["admin", "trainer"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Job erstellen
    job = await training_service.create_job(request)
    return job
```

### 4. Input Validation
```python
from pydantic import BaseModel, validator, Field

class TrainingJobRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1, max_length=100)
    config_name: str = Field(..., regex="^[a-z0-9_-]+$")
    priority: int = Field(1, ge=1, le=5)
    
    @validator("dataset_id")
    def validate_dataset_id(cls, v):
        # Check if dataset exists
        if not dataset_exists(v):
            raise ValueError(f"Dataset {v} not found")
        return v
```

### 3. Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/training/jobs")
@limiter.limit("5/minute")  # Max 5 Jobs pro Minute
async def create_training_job(request: Request, ...):
    ...
```

---

## 📊 Metrics & Monitoring

### Prometheus Metrics
```python
from prometheus_client import Counter, Gauge, Histogram

# Counters
training_jobs_total = Counter(
    'clara_training_jobs_total',
    'Total number of training jobs',
    ['status', 'trainer_type']
)

# Gauges
active_training_jobs = Gauge(
    'clara_active_training_jobs',
    'Number of currently active training jobs'
)

buffer_size = Gauge(
    'clara_learning_buffer_size',
    'Current size of learning buffer'
)

# Histograms
training_duration = Histogram(
    'clara_training_duration_seconds',
    'Training job duration',
    buckets=[60, 300, 600, 1800, 3600, 7200]
)
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "CLARA Training System",
    "panels": [
      {
        "title": "Training Jobs (24h)",
        "targets": [{
          "expr": "rate(clara_training_jobs_total[24h])"
        }]
      },
      {
        "title": "Active Jobs",
        "targets": [{
          "expr": "clara_active_training_jobs"
        }]
      },
      {
        "title": "Learning Buffer Size",
        "targets": [{
          "expr": "clara_learning_buffer_size"
        }]
      },
      {
        "title": "Training Duration (P95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, clara_training_duration_seconds_bucket)"
        }]
      }
    ]
  }
}
```

---

## 🚀 Deployment-Strategie

### Development (Lokaler Start)
```powershell
# 1. Services starten
.\scripts\start_training_backend.ps1

# 2. Frontend starten
python frontend\training_dashboard.py

# 3. Services testen
.\scripts\test_training_services.ps1
```

### Production (Docker Compose)
```yaml
# docker-compose.yml
version: '3.8'

services:
  main_backend:
    build: .
    command: python backend.py
    ports:
      - "45678:45678"
  
  training_backend:
    build: .
    command: python scripts/clara_training_backend.py
    ports:
      - "45680:45680"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  dataset_management:
    build: .
    command: python scripts/clara_dataset_backend.py
    ports:
      - "45681:45681"
  
  model_serving:
    build: .
    command: python scripts/clara_serve_vllm.py
    ports:
      - "45682:45682"
    environment:
      - CLARA_SERVING_ENGINE=vllm
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./configs/prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./configs/grafana:/etc/grafana/provisioning
```

---

## 📋 Implementierungs-Roadmap

### Phase 1: Foundation (Woche 1-2)
- [x] Architektur-Dokument erstellen ✅
- [ ] Training Backend Service (Port 45680) implementieren
- [ ] Job Management System mit PostgreSQL
- [ ] WebSocket Integration für Live-Updates
- [ ] Basis-Tests schreiben

### Phase 2: Dataset Integration (Woche 3-4)
- [ ] Dataset Management Service (Port 45681)
- [ ] UDS3 Hybrid Search Integration
- [ ] Quality Checker implementieren
- [ ] Dataset Registry mit PostgreSQL
- [ ] Frontend: Dataset Explorer

### Phase 3: Continuous Learning (Woche 5-6)
- [ ] ContinuousLoRATrainer erweitern
- [ ] Feedback-Pipeline mit UDS3-Augmentation
- [ ] Auto-Training Trigger-Mechanismen
- [ ] Quality Gates & Rollback-Logik
- [ ] Frontend: Training Monitor

### Phase 4: Model Serving (Woche 7-8)
- [ ] vLLM Multi-LoRa Serving implementieren
- [ ] Adapter Hot-Swap Mechanismus
- [ ] Router-Integration optimieren
- [ ] Load Balancing
- [ ] Frontend: Adapter Manager

### Phase 5: Production Ready (Woche 9-10)
- [ ] Security: JWT, RBAC, Rate Limiting
- [ ] Metrics & Monitoring: Prometheus, Grafana
- [ ] Docker Compose Setup
- [ ] CI/CD Pipeline
- [ ] Load Testing & Performance-Optimierung
- [ ] Umfassende Dokumentation

---

## 🎯 Success Metrics

### System Performance
- **Training Latency:** Job-Start bis Model-Ready < 10 Minuten (für QLoRa, 50 Samples)
- **Throughput:** 5-10 Training Jobs pro Tag (GPU-limitiert)
- **Adapter Quality:** Perplexity-Verbesserung ≥ 5% vs Baseline
- **Uptime:** 99.5% Service Availability

### User Experience
- **Search Response:** UDS3 Hybrid Search < 500ms (P95)
- **Live Updates:** WebSocket Latency < 100ms
- **UI Responsiveness:** Frontend Load Time < 2s

### Learning Quality
- **Feedback Acceptance Rate:** ≥ 60% (Quality-Filter)
- **Auto-Training Success Rate:** ≥ 80%
- **User Satisfaction:** Positive Feedback ≥ 70%

---

## 📚 Referenzen

### Bestehende Komponenten
- `scripts/clara_continuous_learning.py` - Kontinuierliches Lernen
- `scripts/clara_api.py` - FastAPI Basis
- `scripts/clara_train_lora.py` - LoRa Training
- `scripts/clara_serve_vllm.py` - vLLM Serving
- `src/utils/router.py` - Adapter Routing
- `uds3/search/search_api.py` - Hybrid Search

### Dokumentation
- `docs/MICROSERVICES_ARCHITECTURE.md` - Microservices-Design
- `docs/WEBSOCKET_INTEGRATION.md` - WebSocket-Pattern
- `docs/LOAD_TEST_REPORT.md` - Performance-Benchmarks
- `.github/copilot-instructions.md` - Projekt-Status

### Konfigurationen
- `configs/lora_config.yaml` - LoRa Training Config
- `configs/qlora_config.yaml` - QLoRa Training Config
- `configs/router_config.yaml` - Router Config
- `configs/continuous_config.yaml` - Continuous Learning Config

---

**Nächste Schritte:**
1. Todo-Liste durchgehen und priorisieren
2. Training Backend Service implementieren (Phase 1)
3. Iterativ entwickeln mit Tests
4. Continuous Integration nach jedem Feature

**Kontakt:** Development Team  
**Version:** 1.0.0  
**Letzte Aktualisierung:** 24. Oktober 2025
