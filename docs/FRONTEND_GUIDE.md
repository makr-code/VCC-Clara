# Clara AI Frontend - Complete Guide

**Version:** 2.0.0  
**Date:** 2025-11-17  
**Status:** ✅ PRODUCTION READY  
**Maintainer:** VCC Team

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Frontend Applications](#frontend-applications)
4. [Features Reference](#features-reference)
5. [API Integration](#api-integration)
6. [Development Guide](#development-guide)
7. [Troubleshooting](#troubleshooting)

---

## Overview

Clara AI System features **3 separate tkinter GUIs** following **Clean Architecture** and **OOP Best Practices**:

1. **Admin Frontend** (`frontend/admin/app.py`) - System Administration & Monitoring
2. **Data Preparation Frontend** (`frontend/data_preparation/app.py`) - Dataset Management
3. **Training Frontend** (`frontend/training/app.py`) - Training Job Management

### Implementation Status

**All frontends PRODUCTION READY** ✅

- **23 features** implemented across 3 frontends (~3,495 lines of code)
- **Shared component library** for code reuse
- **Backend API integration** (Training: Port 45680, Dataset: Port 45681)
- **Real-time updates** via WebSocket (Training) and polling (Dataset)

### Quick Stats

| Frontend | Features | Lines of Code | Status |
|----------|----------|---------------|--------|
| **Admin** | 9 features | ~1,200 lines | ✅ Production |
| **Training** | 7 features | ~1,100 lines | ✅ Production |
| **Data Prep** | 7 features | ~1,200 lines | ✅ Production |
| **Shared** | Base classes | ~450 lines | ✅ Production |
| **Total** | **23 features** | **~3,495 lines** | ✅ Production |

---

## Architecture

### Directory Structure

```
frontend/
├── shared/                     # Shared Components & Utilities
│   ├── components/             
│   │   ├── base_window.py      # Abstract base class (450 lines)
│   │   └── __init__.py
│   ├── api/                    # Backend API Clients
│   │   ├── training_client.py  # Training Backend Client
│   │   ├── dataset_client.py   # Dataset Backend Client
│   │   └── __init__.py
│   └── utils/                  # Utility functions
│       ├── treeview_utils.py   # Sortable treeview columns
│       ├── progress_utils.py   # Progress dialogs
│       └── __init__.py
├── admin/                      # Admin Frontend
│   ├── app.py                  # Main application (~1,200 lines)
│   └── __init__.py
├── data_preparation/           # Data Preparation Frontend
│   ├── app.py                  # Main application (~1,200 lines)
│   └── __init__.py
├── training/                   # Training Management Frontend
│   ├── app.py                  # Main application (~1,100 lines)
│   └── __init__.py
└── __init__.py
```

### Design Principles

#### 1. Clean Architecture
- **Separation of Concerns:** UI, Business Logic, API Layer separated
- **Dependency Injection:** API clients injected into UI components
- **Single Responsibility:** Each component has one clear purpose

#### 2. OOP Best Practices
- **Inheritance:** All windows extend `BaseWindow` abstract class
- **Encapsulation:** Internal state hidden, public API exposed
- **Polymorphism:** Subclasses override abstract methods

#### 3. Component Reusability
- **Base Window Template:** MenuBar, ToolBar, StatusBar, Sidebar
- **API Clients:** Reusable across all frontends
- **Consistent Styling:** VCC Corporate Identity colors

---

## Frontend Applications

### 1. Admin Frontend

**File:** `frontend/admin/app.py`  
**Purpose:** System administration, monitoring, and management  
**Features:** 9 core features

#### Core Features

| Feature | Function | Description |
|---------|----------|-------------|
| **Real-Time Metrics Dashboard** | `_show_metrics_dashboard()` | Live CPU, Memory, Disk I/O charts (matplotlib) |
| **Enhanced System Logs Viewer** | `_show_system_logs()` | Filter by level, text search, auto-scroll, export |
| **Audit Log Viewer** | `_show_audit_log()` | Action type filtering, user filtering, CSV export |
| **Database Management** | `_manage_databases()` | UDS3 backend control (PostgreSQL, ChromaDB, Neo4j, CouchDB) |
| **System Configuration** | `_manage_system_config()` | Multi-directory browser, file viewer |
| **Service Control** | `_show_service_status()` | Start/Stop/Restart services (PowerShell integration) |
| **Worker Status Display** | `_show_worker_status()` | Detailed worker pool metrics |
| **Exported Files Browser** | `_browse_exported_files()` | View exported datasets with metadata |
| **Training Output Browser** | `_browse_training_outputs()` | Recursive tree of training outputs |

#### Backend Connection

**Dataset Backend API:**
- **Port:** config.dataset_port (default: 45681)
- **Client:** `DatasetAPIClient` from `frontend/shared/api/dataset_client.py`
- **Connection Status:** Displayed in status bar

#### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Menu: File | View | Tools | Help                            │
├─────────────────────────────────────────────────────────────┤
│ [Refresh] [Logs] [Database] [Config] [Services]            │
├──────┬──────────────────────────────────────────────────────┤
│ NAV  │ Main Content Area                                    │
│ - DB │ - Metrics Dashboard                                  │
│ - Cfg│ - Log Viewer                                         │
│ - Svc│ - Configuration Browser                              │
│      │                                                       │
├──────┴──────────────────────────────────────────────────────┤
│ Status: ●Connected | Last update: 10:30:45                  │
└─────────────────────────────────────────────────────────────┘
```

### 2. Training Frontend

**File:** `frontend/training/app.py`  
**Purpose:** Training job management and monitoring  
**Features:** 7 core features

#### Core Features

| Feature | Function | Description |
|---------|----------|-------------|
| **Job Metrics Viewer** | `_show_job_metrics()` | 4 tabs: Loss, Accuracy, Learning Rate, GPU (matplotlib charts) |
| **Job Cancellation** | `_cancel_job()` | Cancel running/queued jobs with status validation |
| **Real-Time Metrics Dashboard** | `_show_metrics_dashboard()` | Live system metrics (CPU, Memory, Disk I/O) |
| **Training Config Manager** | `_manage_training_config()` | YAML editor with validation |
| **Training Output Browser** | `_browse_outputs()` | Recursive file tree with search & type filter |
| **Service Control** | `_show_service_status()` | Start/Stop/Restart training backend |
| **Job Status Filtering** | Built-in | Filter by pending/running/completed/failed |

#### Backend Connection

**Training Backend API:**
- **Port:** config.training_port (default: 45680)
- **Client:** `TrainingAPIClient` from `frontend/shared/api/training_client.py`
- **WebSocket:** Real-time job updates at `ws://localhost:45680/ws/jobs`
- **Connection Status:** 🟢 Live | 🟡 Polling indicator

#### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Menu: File | View | Tools | Help                            │
├─────────────────────────────────────────────────────────────┤
│ [New Job] [Cancel] [Metrics] [Config] [Refresh]  🟢 Live   │
├──────┬──────────────────────────────────────────────────────┤
│ Jobs │ Job List (ID, Status, Progress, Created)             │
│ - All│ ┌────────────────────────────────────────────────┐  │
│ - Run│ │ Job: abc123  Status: Running  Progress: 45%   │  │
│ -Comp│ │ Epoch: 9/20  Loss: 0.234  GPU: 85%            │  │
│      │ └────────────────────────────────────────────────┘  │
├──────┴──────────────────────────────────────────────────────┤
│ Status: 🟢 Connected | Jobs: 3 Running, 5 Completed         │
└─────────────────────────────────────────────────────────────┘
```

### 3. Data Preparation Frontend

**File:** `frontend/data_preparation/app.py`  
**Purpose:** Dataset creation, export, and management  
**Features:** 7 core features

#### Core Features

| Feature | Function | Description |
|---------|----------|-------------|
| **Dataset Export** | `_export_dataset()` | JSONL/Parquet/CSV with progress bar |
| **Dataset Deletion** | `_delete_dataset()` | With confirmation dialog |
| **Dataset Statistics Viewer** | `_show_dataset_stats()` | 3 tabs: Overview, Quality, Distribution |
| **Dataset Status Filtering** | Built-in | Filter by processing/completed/failed |
| **Exported Files Browser** | `_browse_exported_files()` | Metadata extraction, search & format filter |
| **Drag & Drop Upload** | `_setup_drag_drop()` | Multi-file upload with visual feedback |
| **Dataset Creation** | `_create_dataset()` | Create new training datasets |

#### Backend Connection

**Dataset Backend API:**
- **Port:** config.dataset_port (default: 45681)
- **Client:** `DatasetAPIClient` from `frontend/shared/api/dataset_client.py`
- **Polling:** Auto-refresh every 5 seconds

#### UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Menu: File | View | Tools | Help                            │
├─────────────────────────────────────────────────────────────┤
│ [New] [Export] [Delete] [Stats] [Refresh]                  │
├──────┬──────────────────────────────────────────────────────┤
│ DSets│ Dataset List (ID, Name, Status, Size, Created)       │
│ - All│ ┌────────────────────────────────────────────────┐  │
│ -Proc│ │ Drop files here to upload                      │  │
│ -Comp│ │                   📁                            │  │
│      │ └────────────────────────────────────────────────┘  │
├──────┴──────────────────────────────────────────────────────┤
│ Status: ●Connected | Datasets: 12 total, 3 processing       │
└─────────────────────────────────────────────────────────────┘
```

---

## Features Reference

### Complete Feature List

All 23 features across 3 frontends:

#### High-Priority Features (6 features)
1. ✅ **Dataset Export** (Data Prep) - JSONL/Parquet/CSV with progress
2. ✅ **Dataset Deletion** (Data Prep) - With confirmation
3. ✅ **Job Cancellation** (Training) - Status validation
4. ✅ **Job Metrics Viewer** (Training) - 4 tabs, matplotlib charts
5. ✅ **Service Control** (Admin/Training) - PowerShell integration
6. ✅ **Job Status Filtering** (Training) - Built-in filter

#### Medium-Priority Features (8 features)
7. ✅ **Dataset Status Filtering** (Data Prep) - Processing/Completed/Failed
8. ✅ **Worker Status Display** (Admin) - ~150 lines, detailed metrics
9. ✅ **Dataset Statistics Viewer** (Data Prep) - ~200 lines, 3 tabs
10. ✅ **Training Config Manager** (Training) - ~270 lines, YAML editor
11. ✅ **Training Output Files Browser** (Training/Admin) - ~200 lines, recursive tree
12. ✅ **Exported Files Browser** (Data Prep/Admin) - ~180 lines, metadata
13. ✅ **Database Management UI** (Admin) - ~250 lines, 4 UDS3 backends
14. ✅ **System Configuration Manager** (Admin) - ~280 lines, multi-directory

#### UX Enhancements (3 features)
15. ✅ **Keyboard Shortcuts** - 20+ shortcuts across all frontends
16. ✅ **Treeview Column Sorting** - Click column headers to sort
17. ✅ **Progress Indicators** - Progress dialogs with % and download progress

#### Optional Features (4 features)
18. ✅ **Real-Time Metrics Dashboard** (Admin/Training) - ~250 lines each
19. ✅ **Enhanced System Logs Viewer** (Admin) - ~220 lines
20. ✅ **Audit Log Viewer** (Admin) - ~200 lines
21. ✅ **Drag & Drop File Upload** (Data Prep) - ~190 lines
22. ✅ **Search & Filter Bars** (Training/Data Prep) - ~65 lines
23. ✅ **Exported Files Search** (Data Prep/Admin) - Integrated

### Keyboard Shortcuts

#### Global Shortcuts (All Frontends)
- **F5** - Refresh data
- **Ctrl+R** - Refresh data
- **Ctrl+L** - Open logs
- **Ctrl+B** - Toggle sidebar
- **F1** - Show help
- **Escape** - Close dialogs

#### Training Frontend
- **Ctrl+N** - New training job
- **Ctrl+K** - Cancel selected job
- **Ctrl+M** - Show job metrics
- **Ctrl+O** - Browse training outputs
- **Shift+C** - Training config manager

#### Data Preparation Frontend
- **Ctrl+N** - New dataset
- **Ctrl+E** - Export selected dataset
- **Ctrl+S** - Show dataset statistics
- **Delete** - Delete selected dataset
- **Shift+E** - Browse exported files

#### Admin Frontend
- **Ctrl+D** - Database management
- **Shift+S** - System configuration
- **Ctrl+X** - Service control
- **Ctrl+R** - Real-time metrics
- **Ctrl+C** - View system config

---

## API Integration

### Training Backend API Client

**File:** `frontend/shared/api/training_client.py`

```python
from frontend.shared.api.training_client import TrainingAPIClient

# Initialize client
client = TrainingAPIClient(base_url="http://localhost:45680")

# Create training job
job = client.create_job(config={
    "model_name": "llama-2-7b",
    "dataset_id": "abc123",
    "epochs": 10
})

# Get job status
status = client.get_job(job_id="job_abc123")

# Cancel job
client.cancel_job(job_id="job_abc123")

# List all jobs
jobs = client.list_jobs()
```

### Dataset Backend API Client

**File:** `frontend/shared/api/dataset_client.py`

```python
from frontend.shared.api.dataset_client import DatasetAPIClient

# Initialize client
client = DatasetAPIClient(base_url="http://localhost:45681")

# Create dataset
dataset = client.create_dataset(name="my_dataset", source="upload")

# Export dataset
client.export_dataset(
    dataset_id="ds_abc123",
    format="parquet",
    output_path="exports/dataset.parquet"
)

# Get dataset statistics
stats = client.get_statistics(dataset_id="ds_abc123")

# Delete dataset
client.delete_dataset(dataset_id="ds_abc123")
```

### WebSocket Integration (Training)

**Real-time job updates:**

```python
from frontend.shared.api.ingestion_websocket import IngestionWebSocketClient

# Initialize WebSocket client
ws_client = IngestionWebSocketClient(
    url="ws://localhost:45680/ws/jobs",
    on_message=handle_job_update
)

# Connect
ws_client.connect()

# Handle updates
def handle_job_update(message):
    job_id = message.get("job_id")
    status = message.get("status")
    progress = message.get("progress")
    # Update UI...
```

---

## Development Guide

### Running the Frontends

**Admin Frontend:**
```bash
python frontend/admin/app.py
```

**Training Frontend:**
```bash
python frontend/training/app.py
```

**Data Preparation Frontend:**
```bash
python frontend/data_preparation/app.py
```

### Prerequisites

**Required:**
- Python 3.8+
- tkinter (usually included with Python)
- Backend services running (Training: 45680, Dataset: 45681)

**Optional:**
- tkinterdnd2 (for drag & drop) - `pip install tkinterdnd2`
- matplotlib (for charts) - `pip install matplotlib`
- psutil (for metrics) - `pip install psutil`

### Creating a New Frontend

1. **Extend BaseWindow:**

```python
from frontend.shared.components.base_window import BaseWindow

class MyWindow(BaseWindow):
    def __init__(self):
        super().__init__(title="My Window", width=1200, height=800)
        
    def setup_toolbar_actions(self):
        # Add toolbar buttons
        self.add_toolbar_button(
            text="My Action",
            command=self._my_action,
            icon="🔨"
        )
        
    def setup_sidebar_content(self):
        # Add sidebar navigation
        self.add_sidebar_button("Section 1", self._show_section1)
        self.add_sidebar_button("Section 2", self._show_section2)
        
    def setup_main_content(self):
        # Create main content area
        label = tk.Label(self.main_content, text="Main Content")
        label.pack(pady=20)
```

2. **Add API Client:**

```python
from frontend.shared.api.training_client import TrainingAPIClient

class MyWindow(BaseWindow):
    def __init__(self):
        super().__init__(...)
        self.api_client = TrainingAPIClient()
```

3. **Implement Features:**

```python
def _my_action(self):
    """Example action"""
    try:
        result = self.api_client.some_method()
        self.show_success("Action completed!")
    except Exception as e:
        self.show_error(f"Error: {e}")
```

### Shared Utilities

#### Sortable Treeview

```python
from frontend.shared.utils.treeview_utils import make_treeview_sortable

# Create treeview
tree = ttk.Treeview(parent, columns=("col1", "col2"))

# Make columns sortable
make_treeview_sortable(tree, columns=["col1", "col2"])
```

#### Progress Dialog

```python
from frontend.shared.utils.progress_utils import show_progress_dialog

# Show progress dialog
dialog = show_progress_dialog(
    parent=self,
    title="Exporting",
    message="Exporting dataset...",
    total=100
)

# Update progress
dialog.update_progress(50, "50% complete")

# Close when done
dialog.close()
```

---

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to backend"

**Cause:** Backend service not running

**Solution:**
```bash
# Check if backend is running
netstat -ano | findstr :45680  # Windows
lsof -i :45680                 # Linux/Mac

# Start backend
python -m backend.training.app
python -m backend.datasets.app
```

#### 2. "WebSocket connection failed"

**Cause:** Training backend not supporting WebSocket

**Solution:**
- System automatically falls back to polling (5s interval)
- Check Training Backend logs for WebSocket errors
- Connection indicator shows: 🟢 Live (WebSocket) or 🟡 Polling (fallback)

#### 3. "Drag & Drop not working"

**Cause:** tkinterdnd2 not installed

**Solution:**
```bash
pip install tkinterdnd2
```

**Note:** System gracefully degrades to double-click file selection if tkinterdnd2 unavailable

#### 4. "Charts not displaying"

**Cause:** matplotlib not installed

**Solution:**
```bash
pip install matplotlib
```

#### 5. "Port already in use"

**Cause:** Another service using default ports

**Solution:**
```bash
# Change ports via environment variables
export CLARA_TRAINING_PORT=8080
export CLARA_DATASET_PORT=8081

# Or update config/development.py
```

### Debug Mode

**Enable debug logging:**

```python
# Set environment variable
export CLARA_DEBUG=true
export CLARA_LOG_LEVEL=DEBUG

# Run frontend
python frontend/training/app.py
```

### Performance Tips

1. **Disable auto-refresh** if dealing with large datasets
2. **Use pagination** for large result sets
3. **Close unused metric dashboards** to reduce CPU usage
4. **Limit chart history** to 60 points (default)

---

## Related Documentation

- **[CONFIGURATION_REFERENCE.md](./CONFIGURATION_REFERENCE.md)** - Backend configuration options
- **[UDS3_STATUS.md](./UDS3_STATUS.md)** - UDS3 integration status
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Overall implementation status
- **[DOCUMENTATION_TODO.md](./DOCUMENTATION_TODO.md)** - Ongoing documentation tasks

### Historical Documentation (Archived)

For historical context and implementation details, see archived documentation:

- **docs/archive/frontend/** - Historical completion reports and analysis
  - FRONTEND_IMPLEMENTATION_COMPLETE.md
  - FRONTEND_IMPLEMENTATION_SUMMARY.md
  - FRONTEND_DEVELOPMENT_COMPLETE_SUMMARY.md
  - FRONTEND_FUNCTIONS_ANALYSIS.md

---

**Last Updated:** 2025-11-17  
**Maintainer:** VCC Documentation Team  
**Version:** 2.0.0 (Consolidated from 6 separate documents)
