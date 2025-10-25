# Clara AI Frontend Architecture

**Version:** 2.0.0  
**Date:** 25. Oktober 2025  
**Status:** ✅ PRODUCTION READY

## 📋 Overview

Clara AI System features **3 separate tkinter GUIs** following **Clean Architecture** and **OOP Best Practices**:

1. **Admin Frontend** (`frontend/admin/`) - System Administration
2. **Data Preparation Frontend** (`frontend/data_preparation/`) - Dataset Management
3. **Training Frontend** (`frontend/training/`) - Training Job Management

## 🏗️ Architecture

### Directory Structure
```
frontend/
├── shared/                     # Shared Components
│   ├── components/             
│   │   ├── base_window.py      # Abstract base class for all windows
│   │   └── __init__.py
│   ├── api/                    
│   │   ├── training_client.py  # Training Backend API Client
│   │   ├── dataset_client.py   # Dataset Backend API Client
│   │   └── __init__.py
│   └── utils/                  # Utility functions
├── admin/                      
│   ├── app.py                  # Admin Frontend Application
│   └── __init__.py
├── data_preparation/           
│   ├── app.py                  # Data Preparation Application
│   └── __init__.py
├── training/                   
│   ├── app.py                  # Training Management Application
│   └── __init__.py
└── __init__.py
```

## 🎨 Design Principles

### 1. **Clean Architecture**
- **Separation of Concerns:** UI, Business Logic, API Layer separated
- **Dependency Injection:** API clients injected into UI components
- **Single Responsibility:** Each component has one clear purpose

### 2. **OOP Best Practices**
- **Inheritance:** All windows extend `BaseWindow` abstract class
- **Encapsulation:** Internal state hidden, public API exposed
- **Polymorphism:** Subclasses override abstract methods

### 3. **Component Reusability**
- **Base Window Template:** MenuBar, ToolBar, StatusBar, Sidebar
- **API Clients:** Reusable across all frontends
- **Consistent Styling:** VCC Corporate Identity colors

## 🧩 Shared Components

### BaseWindow Class

**File:** `frontend/shared/components/base_window.py`

**Abstract Base Class** providing standard UI infrastructure:

```python
class BaseWindow(tk.Tk, ABC):
    """
    Abstract Base Window
    
    Provides:
    - Menu Bar with File, View, Tools, Help menus
    - Tool Bar with action buttons
    - Left Sidebar for navigation
    - Main content area
    - Status Bar with connection status
    - VCC Corporate Identity styling
    """
    
    @abstractmethod
    def setup_toolbar_actions(self):
        """Subclass must implement toolbar buttons"""
        pass
    
    @abstractmethod
    def setup_sidebar_content(self):
        """Subclass must implement sidebar navigation"""
        pass
    
    @abstractmethod
    def setup_main_content(self):
        """Subclass must implement main content area"""
        pass
```

**Features:**
- ✅ **Standard Menu Bar:** File, View, Tools, Help
- ✅ **Customizable Toolbar:** Left and right button areas
- ✅ **Collapsible Sidebar:** Navigation with hover effects
- ✅ **Status Bar:** Connection status + message area
- ✅ **Theming:** VCC blue color scheme
- ✅ **Utility Methods:** show_info(), show_error(), confirm(), etc.

### API Clients

#### TrainingAPIClient

**File:** `frontend/shared/api/training_client.py`

**Purpose:** Communication with Training Backend (Port 45680)

**Methods:**
```python
client = TrainingAPIClient()

# Health check
health = client.health_check()

# Job management
job = client.create_job(trainer_type="lora", config_path="...")
job_details = client.get_job(job_id)
jobs = client.list_jobs(status="running")
client.cancel_job(job_id)

# Metrics & monitoring
metrics = client.get_job_metrics(job_id)
workers = client.get_worker_status()

# Connection check
is_online = client.is_connected()
```

#### DatasetAPIClient

**File:** `frontend/shared/api/dataset_client.py`

**Purpose:** Communication with Dataset Backend (Port 45681)

**Methods:**
```python
client = DatasetAPIClient()

# Health check
health = client.health_check()

# Dataset management
dataset = client.create_dataset(
    name="my_dataset",
    query_text="search query",
    top_k=100
)
dataset_details = client.get_dataset(dataset_id)
datasets = client.list_datasets()
client.delete_dataset(dataset_id)

# Export
result = client.export_dataset(dataset_id, format="jsonl")

# Connection check
is_online = client.is_connected()
```

## 🖥️ Frontend Applications

### 1. Admin Frontend

**File:** `frontend/admin/app.py`  
**Port:** N/A (connects to both backends)  
**Purpose:** System Administration & Monitoring

**Features:**
- 🏠 **Dashboard:** Real-time service status monitoring
- 🔧 **Service Control:** Start/Stop/Restart services
- ⚙️ **Configuration:** System configuration management
- 📊 **Metrics:** Performance metrics dashboard
- 📋 **Logs:** System log viewer with filtering
- 👥 **Users:** User management (future)
- 🔐 **Security:** Security settings
- 📜 **Audit Log:** Security audit trail
- 🚨 **Alerts:** System alerts and notifications

**UI Components:**
- **Service Status Cards:** Live status for Training, Dataset, UDS3
- **Metrics Notebook:** Performance, Jobs, Datasets tabs
- **Log Viewer:** Colored logs with level filtering
- **Control Toolbar:** Start/Stop/Restart all services

**Launch:**
```bash
python -m frontend.admin.app
```

### 2. Data Preparation Frontend

**File:** `frontend/data_preparation/app.py`  
**Port:** Connects to 45681 (Dataset Backend)  
**Purpose:** Dataset Creation & Management

**Features:**
- 📚 **Dataset List:** All datasets with search/filter
- ➕ **Create Dataset:** Visual dataset creation wizard
- 🔍 **UDS3 Search:** Integrated search interface
- 📤 **Export:** Multiple formats (JSONL, Parquet, CSV)
- 📊 **Statistics:** Dataset statistics and analytics
- 🗄️ **File Browser:** Exported file management
- 🎯 **Query Builder:** Visual query builder (future)

**UI Components:**
- **Dataset TreeView:** Searchable dataset list
- **Details Panel:** Dataset info, query, preview
- **Creation Dialog:** Multi-step dataset wizard
- **Export Controls:** Format selection and export

**Launch:**
```bash
python -m frontend.data_preparation.app
```

### 3. Training Frontend

**File:** `frontend/training/app.py`  
**Port:** Connects to 45680 (Training Backend)  
**Purpose:** Training Job Management

**Features:**
- 📋 **Job List:** All training jobs with status
- ➕ **Create Job:** Job creation dialog
- ▶️ **Job Control:** Cancel/Pause/Resume jobs
- 📊 **Metrics:** Training metrics visualization
- 👷 **Workers:** Worker pool status
- ⚙️ **Config Manager:** Training config management
- 📁 **Output Files:** Model output browser
- 🔄 **Auto-Refresh:** Live job updates

**UI Components:**
- **Job TreeView:** Filterable job list with progress
- **Details Panel:** Job info, logs, metrics
- **Creation Dialog:** Config file selection wizard
- **Auto-Refresh:** 5-second polling toggle

**Launch:**
```bash
python -m frontend.training.app
```

## 🎨 UI Standards

### VCC Corporate Identity Colors

```python
COLORS = {
    'primary': '#0066CC',      # VCC Blue
    'secondary': '#004499',    # Dark Blue
    'success': '#28A745',      # Green
    'warning': '#FFC107',      # Yellow
    'danger': '#DC3545',       # Red
    'background': '#F5F5F5',   # Light Gray
    'sidebar': '#2C3E50',      # Dark Gray
    'text': '#212529',         # Almost Black
    'text_light': '#FFFFFF',   # White
    'border': '#DEE2E6'        # Border Gray
}
```

### Layout Components

**Standard Window Layout:**
```
┌────────────────────────────────────────────┐
│  Menu Bar: File | View | Tools | Help     │
├────────────────────────────────────────────┤
│  Tool Bar: [Actions Left]  [Actions Right]│
├─────────┬──────────────────────────────────┤
│ Sidebar │  Main Content Area               │
│         │                                  │
│ [Nav 1] │  ┌─────────────────────────┐    │
│ [Nav 2] │  │  Content Frames         │    │
│ [Nav 3] │  │  (Panes, Notebooks,    │    │
│ [Nav 4] │  │   TreeViews, etc.)     │    │
│         │  └─────────────────────────┘    │
├─────────┴──────────────────────────────────┤
│  Status Bar: Message | Connection Status   │
└────────────────────────────────────────────┘
```

### Component Guidelines

**Sidebar Navigation:**
- Icon + Text buttons (e.g., "📋 All Jobs")
- Hover effect (background change to primary color)
- Flat relief, left-aligned text
- 20px horizontal padding, 12px vertical padding

**Toolbar Buttons:**
- Icon + Short text (e.g., "➕ New Job")
- Primary blue background
- White text
- Flat relief, 15px horizontal padding

**Status Bar:**
- Left: Status message (expandable)
- Right: Connection indicator (🟢/🔴 + text)
- Dark background with white text

**TreeView Lists:**
- Headings with sortable columns
- Colored tags for status (green, yellow, red)
- Scrollbars (vertical + horizontal)
- Selection handlers for detail views

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.13+
pip install tkinter  # Usually included with Python
pip install requests
```

### Launch Single Frontend

```bash
# Admin Frontend
python -m frontend.admin.app

# Data Preparation
python -m frontend.data_preparation.app

# Training Management
python -m frontend.training.app
```

### Launch All Frontends

**PowerShell:**
```powershell
.\launch_frontend.ps1
```

**Options:**
1. Admin Frontend
2. Data Preparation Frontend
3. Training Frontend
4. Launch All Frontends
5. Start Backend Services
0. Exit

### Launch with Backends

```powershell
# 1. Start backends
$env:CLARA_ENVIRONMENT="development"
Start-Process python -ArgumentList "-m","backend.training.app"
Start-Process python -ArgumentList "-m","backend.datasets.app"

# 2. Wait for startup
Start-Sleep -Seconds 5

# 3. Launch frontend
python -m frontend.training.app
```

## 🔧 Development Guide

### Creating Custom Frontend

**1. Extend BaseWindow:**

```python
from frontend.shared.components.base_window import BaseWindow

class MyFrontend(BaseWindow):
    def __init__(self):
        super().__init__("My Custom Frontend", width=1200, height=800)
    
    def setup_toolbar_actions(self):
        self.add_toolbar_button("➕ Action", self.my_action, side="left")
    
    def setup_sidebar_content(self):
        self.add_sidebar_button("🏠 Home", self.show_home, icon="🏠")
    
    def setup_main_content(self):
        # Add your main UI components
        label = ttk.Label(self.content_area, text="Hello World!")
        label.pack()
    
    def my_action(self):
        self.show_info("Info", "Action executed!")
    
    def show_home(self):
        print("Navigate to home")
```

**2. Add API Integration:**

```python
from frontend.shared.api.training_client import TrainingAPIClient

class MyFrontend(BaseWindow):
    def __init__(self):
        self.api_client = TrainingAPIClient()
        super().__init__("My Frontend")
        self.check_connection()
    
    def check_connection(self):
        def check():
            try:
                health = self.api_client.health_check()
                self.update_connection_status("Connected", connected=True)
            except:
                self.update_connection_status("Disconnected", connected=False)
            
            self.after(10000, self.check_connection)
        
        threading.Thread(target=check, daemon=True).start()
```

## 📊 Features Summary

| Feature | Admin | Data Prep | Training |
|---------|-------|-----------|----------|
| **Service Monitoring** | ✅ Real-time | ⏳ Basic | ⏳ Basic |
| **Job Management** | ⏳ View Only | ❌ N/A | ✅ Full CRUD |
| **Dataset Management** | ⏳ View Only | ✅ Full CRUD | ❌ N/A |
| **Metrics Dashboard** | ✅ Multi-service | ✅ Datasets | ✅ Training |
| **Log Viewer** | ✅ System-wide | ⏳ Dataset logs | ✅ Job logs |
| **User Management** | 🔜 Planned | ❌ N/A | ❌ N/A |
| **Configuration** | ✅ System config | ⏳ Export config | ✅ Training config |
| **Auto-Refresh** | ✅ 5s polling | ⏳ Manual | ✅ Toggleable |

Legend: ✅ Implemented | ⏳ Partial | 🔜 Planned | ❌ N/A

## 🎯 Best Practices

### 1. **Threading for API Calls**

Always use background threads for API calls to keep UI responsive:

```python
def refresh_data(self):
    def fetch():
        try:
            data = self.api_client.list_items()
            self.after(0, lambda: self.update_ui(data))
        except Exception as e:
            self.after(0, lambda: self.show_error("Error", str(e)))
    
    threading.Thread(target=fetch, daemon=True).start()
```

### 2. **Error Handling**

Always handle API errors gracefully:

```python
try:
    result = self.api_client.create_job(...)
    if result.get("success"):
        self.show_info("Success", "Job created!")
    else:
        self.show_error("Error", result.get("message"))
except Exception as e:
    self.show_error("Connection Error", f"Failed: {e}")
```

### 3. **Status Updates**

Update status bar to inform users:

```python
self.update_status("Loading jobs...")
# ... perform operation ...
self.update_status(f"Loaded {count} jobs")
```

### 4. **Confirmation Dialogs**

Always confirm destructive actions:

```python
if self.confirm("Delete Job", "Are you sure?"):
    self.delete_job()
```

## 🚨 Known Limitations

### Current Limitations

1. **No WebSocket Support:** Uses polling for updates (5s interval)
2. **Single-User:** No multi-user session management
3. **Limited Metrics:** Basic metrics visualization
4. **No Drag & Drop:** File selection via dialogs only
5. **No Dark Mode:** Light theme only

### Planned Enhancements (v2.1.0)

- [ ] WebSocket real-time updates
- [ ] Dark mode support
- [ ] Drag & drop file uploads
- [ ] Advanced metrics dashboards (matplotlib integration)
- [ ] User authentication UI
- [ ] Configuration file editor
- [ ] Export job/dataset history to CSV
- [ ] Keyboard shortcuts
- [ ] Dockable panels
- [ ] Multi-monitor support

## 📞 Support & Resources

### Documentation
- **Frontend Architecture:** This document
- **Backend APIs:** `http://localhost:45680/docs`, `http://localhost:45681/docs`
- **Component Reference:** See docstrings in `base_window.py`

### Development
- **Code Style:** PEP 8 + Google docstrings
- **Testing:** Manual testing + future automated UI tests
- **Dependencies:** tkinter (stdlib), requests

---

## 🏆 Summary

Clara AI v2.0 features **3 production-ready tkinter frontends** following **Clean Architecture** and **OOP Best Practices**:

✅ **Shared Component Library** with reusable BaseWindow  
✅ **API Client Layer** for backend communication  
✅ **Consistent UI/UX** with VCC Corporate Identity  
✅ **Modular Architecture** for easy maintenance  
✅ **Professional Layout** with MenuBar, ToolBar, StatusBar, Sidebar  

**All frontends are ready for production use!** 🚀

---

**Created:** 25. Oktober 2025  
**Version:** 2.0.0  
**Status:** 🚀 PRODUCTION READY
