# CLARA System - Startup Scripts

**Quick Start Guide für alle PowerShell Startup Scripts**

---

## 📜 Verfügbare Scripts

| Script | Beschreibung | Verwendung |
|--------|--------------|------------|
| `start_clara.ps1` | **All-in-One** - Startet Backends + Frontends | Development Setup |
| `start_backends.ps1` | Nur Backend Services starten | Backend-Entwicklung |
| `stop_backends.ps1` | Alle Backend Services stoppen | Cleanup |
| `launch_frontend.ps1` | Interaktives Frontend-Menü | Frontend-Auswahl |

---

## 🚀 Quick Start

### Option 1: Komplettes System starten

```powershell
.\start_clara.ps1
```

**Startet automatisch:**
- ✅ Training Backend (Port 45680)
- ✅ Dataset Backend (Port 45681)
- ✅ Admin Frontend (GUI)
- ✅ Data Preparation Frontend (GUI)
- ✅ Training Frontend (GUI)

**Wartet:** 5 Sekunden zwischen Backend-Start und Frontend-Launch

---

### Option 2: Nur Backends starten

```powershell
.\start_backends.ps1
```

**Öffnet:** 2 PowerShell-Fenster mit Backend-Logs

**Überprüft:**
- Health Check beider Services
- Ports verfügbar
- Service-Status

---

### Option 3: Nur Frontends starten

```powershell
.\start_clara.ps1 -FrontendsOnly
```

**Voraussetzung:** Backends müssen bereits laufen

---

### Option 4: Interaktive Auswahl

```powershell
.\launch_frontend.ps1
```

**Menü:**
```
1) Admin Frontend - System Administration
2) Data Preparation - Dataset Management
3) Training Frontend - Training Management
4) Launch All Frontends
5) Start Backend Services
0) Exit
```

---

## 🛑 System Stoppen

### Backends stoppen

```powershell
.\stop_backends.ps1
```

**Funktionsweise:**
1. Findet alle Python-Prozesse mit `backend.training.app` oder `backend.datasets.app`
2. Versucht graceful shutdown (CloseMainWindow)
3. Force kill nach 2 Sekunden falls nötig
4. Verifiziert Health Endpoints (sollten nicht mehr antworten)

### Frontends schließen

**Manuell:** Einfach GUI-Fenster schließen (X-Button)

---

## 🔧 Parameter & Optionen

### `start_clara.ps1`

```powershell
# Nur Backends starten (keine GUIs)
.\start_clara.ps1 -BackendsOnly

# Nur Frontends starten (Backends laufen bereits)
.\start_clara.ps1 -FrontendsOnly

# Alles starten (Standard)
.\start_clara.ps1
```

### `start_backends.ps1`

**Keine Parameter** - Startet immer beide Backends

**Features:**
- ✅ Erkennt bereits laufende Services
- ✅ Überspringt Start wenn Port belegt
- ✅ Health Check nach Start
- ✅ Zeigt Service-Status an

---

## 📊 Backend Services

### Training Backend (Port 45680)

**API Endpoints:**
- `GET /health` - Health Check
- `POST /api/training/jobs` - Training Job erstellen
- `GET /api/training/jobs/{id}` - Job Details
- `GET /api/training/jobs/list` - Alle Jobs auflisten
- `DELETE /api/training/jobs/{id}` - Job abbrechen
- `WebSocket /api/training/ws` - Live Updates

**Features:**
- Worker Pool: 2 concurrent jobs
- Job Queue Management
- Status Tracking
- Progress Monitoring

### Dataset Backend (Port 45681)

**API Endpoints:**
- `GET /health` - Health Check
- `POST /api/datasets` - Dataset erstellen
- `GET /api/datasets/{id}` - Dataset Details
- `GET /api/datasets` - Alle Datasets auflisten
- `DELETE /api/datasets/{id}` - Dataset löschen
- `POST /api/datasets/{id}/export` - Dataset exportieren

**Features:**
- UDS3 Integration (optional)
- Multi-Format Export (JSONL, Parquet, CSV)
- Search Query Builder

---

## 🖥️ Frontend Applications

### 1. Admin Frontend

**Features:**
- Service Status Monitoring (Training, Dataset, UDS3)
- Metrics Dashboard
- System Log Viewer
- Service Control (Start/Stop/Restart)

**Toolbar:**
- Start All Services
- Stop All Services
- Restart All Services
- View Metrics
- View Logs

### 2. Data Preparation Frontend

**Features:**
- Dataset List mit Search/Filter
- Dataset Creation Wizard
- Export Controls (JSONL, Parquet, CSV)
- UDS3 Search Integration

**Toolbar:**
- New Dataset
- Refresh List
- Export Dataset
- Search UDS3

### 3. Training Frontend

**Features:**
- Training Job List mit Filtern
- Job Creation Dialog
- Auto-Refresh (5s Polling)
- Job Metrics Viewer

**Toolbar:**
- New Job
- Refresh List
- Worker Status
- View Metrics

---

## 🐛 Troubleshooting

### Problem: "Port already in use"

**Symptom:**
```
[!!] Training Backend already running on port 45680
```

**Lösung:**
```powershell
# Backends stoppen
.\stop_backends.ps1

# Neu starten
.\start_backends.ps1
```

### Problem: Backend startet nicht

**Check 1: Python Environment**
```powershell
python --version
# Sollte: Python 3.8+
```

**Check 2: Dependencies**
```powershell
pip install -r requirements.txt
```

**Check 3: Ports frei**
```powershell
# Port 45680 checken
netstat -ano | findstr :45680

# Port 45681 checken
netstat -ano | findstr :45681
```

### Problem: Frontend verbindet nicht

**Check 1: Backends laufen**
```powershell
# Browser öffnen:
# http://localhost:45680/health
# http://localhost:45681/health
```

**Check 2: Firewall**
```
Windows Firewall → Python erlauben
```

### Problem: "SecurityConfig deprecated" Warning

**Status:** ⚠️ **NICHT KRITISCH** - Backends funktionieren trotzdem

**Behebung (optional):**
```python
# In betroffenen Dateien:
# Alt:
from shared.security.config import SecurityConfig

# Neu:
from config import config
```

### Problem: "UDS3 not available"

**Status:** ⚠️ **NICHT KRITISCH** - UDS3 ist optional

**Bedeutung:**
- Dataset Search über UDS3 deaktiviert
- Alle anderen Features funktionieren normal
- Datasets können manuell erstellt werden

**UDS3 aktivieren (optional):**
```powershell
# UDS3 Backend starten (separater Prozess)
cd ..\uds3
python -m uds3.main
```

---

## 📝 Logs & Debugging

### Backend Logs

**Location:** PowerShell-Fenster der Backends

**Log Levels:**
- `INFO` - Normale Operationen
- `WARNING` - Nicht-kritische Probleme
- `ERROR` - Fehler
- `DEBUG` - Detaillierte Debug-Info

### Frontend Logs

**Location:** Python-Prozess (bei Fehlern)

**Anzeige:**
```powershell
# Frontend im Terminal starten (für Logs):
python -m frontend.admin.app
```

---

## 🔒 Security Notes

### Development Mode

**Aktueller Status:**
- ✅ CORS: `*` (alle Origins erlaubt)
- ⚠️ JWT: Optional (Dev-User fallback)
- ⚠️ Auth: Deaktiviert für Development

**Production Changes:**
```python
# backend/training/app.py
# backend/datasets/app.py

# CORS auf spezifische Origins beschränken:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend-URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# JWT aktivieren:
# shared/auth/middleware.py konfigurieren
```

---

## 📚 Weitere Dokumentation

- **Frontend Architecture:** `docs/FRONTEND_ARCHITECTURE.md`
- **Backend Training:** `docs/PHASE_1_COMPLETION_REPORT.md`
- **Dataset Backend:** `docs/DATASET_BACKEND_IMPLEMENTATION.md`
- **Full Implementation:** `docs/FRONTEND_IMPLEMENTATION_COMPLETE.md`

---

## 🎯 Typical Workflows

### 1. Development Workflow

```powershell
# Morning: Alles starten
.\start_clara.ps1

# Work: Frontends nutzen
# - Admin: Service Monitoring
# - Data Prep: Datasets erstellen
# - Training: Jobs starten

# Evening: Backends stoppen
.\stop_backends.ps1
# Frontends: Fenster schließen
```

### 2. Backend Development

```powershell
# Nur Backends starten (für API Tests)
.\start_backends.ps1

# API Tests mit curl/Postman
curl http://localhost:45680/health
curl http://localhost:45681/health

# Code ändern → Backend neu starten
.\stop_backends.ps1
.\start_backends.ps1
```

### 3. Frontend Development

```powershell
# Backends starten (einmalig)
.\start_backends.ps1

# Frontend testen (mehrfach)
python -m frontend.admin.app

# Code ändern → Frontend neu starten
# (Backends laufen weiter)
```

---

## ✅ Status Check

### Alle Services prüfen

```powershell
# Training Backend
curl http://localhost:45680/health

# Dataset Backend
curl http://localhost:45681/health

# Prozesse anzeigen
Get-Process python | Where-Object { $_.CommandLine -match "backend" }
```

**Expected Output:**
```json
// Training Backend
{
  "status": "healthy",
  "service": "clara_training_backend",
  "port": 45680,
  "active_jobs": 0,
  "max_concurrent_jobs": 2
}

// Dataset Backend
{
  "status": "healthy",
  "service": "clara_dataset_backend",
  "port": 45681,
  "datasets_count": 0,
  "uds3_available": false
}
```

---

**Created:** 25. Oktober 2025  
**Status:** ✅ PRODUCTION READY  
**Version:** 2.0.0
