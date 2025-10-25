# Frontend Features Quick Reference

**Date:** 25. Oktober 2025  
**Status:** ✅ Production Ready

---

## Overview

All frontend features have been fully implemented and tested. This guide provides quick access to feature locations and usage.

---

## Training Frontend (`frontend/training/app.py`)

### High-Priority Features
| Feature | Function | Location | Description |
|---------|----------|----------|-------------|
| **Job Cancellation** | `cancel_selected_job()` | Lines ~450 | Cancel running/pending jobs with status validation |
| **Job Metrics Viewer** | `view_job_metrics()` | Lines ~480 | 4-tab window with loss/accuracy/lr/gradient charts |
| **Service Control** | `start_service()`, `stop_service()`, `restart_service()` | Lines ~550 | PowerShell integration for backend control |

### Medium-Priority Features
| Feature | Function | Location | Description |
|---------|----------|----------|-------------|
| **Worker Status** | `_show_worker_status_window()` | Lines ~620 | Detailed worker pool metrics (I/O + CPU) |
| **Config Manager** | `show_config_manager()` | Lines ~780 | YAML editor with validation + backup |
| **Output Files Browser** | `show_output_files()` | Lines ~1050 | Recursive models/ browser with file ops |

### Usage
```bash
# Start Training Frontend
python frontend/training/main.py
```

**Common Actions:**
- Cancel job: Select job → Click "🚫 Cancel Job"
- View metrics: Select job → Click "📊 View Metrics"
- Manage configs: Click "⚙️ Manage Configs" toolbar button
- Browse outputs: Click "📁 Output Files" toolbar button

---

## Data Preparation Frontend (`frontend/data_preparation/app.py`)

### High-Priority Features
| Feature | Function | Location | Description |
|---------|----------|----------|-------------|
| **Dataset Export** | `export_selected_dataset()` | Lines ~420 | Export to JSONL/Parquet/CSV with progress |
| **Dataset Deletion** | `delete_selected_dataset()` | Lines ~490 | Safe deletion with confirmation dialog |

### Medium-Priority Features
| Feature | Function | Location | Description |
|---------|----------|----------|-------------|
| **Status Filtering** | `show_processing_datasets()`, etc. | Lines ~540 | Filter by processing/completed/failed |
| **Statistics Viewer** | `show_statistics()` | Lines ~600 | 3-tab stats (Overview, Quality, Search Types) |
| **Exported Files Browser** | `show_exported_files()` | Lines ~800 | Browse data/exports/ with metadata |

### Usage
```bash
# Start Data Prep Frontend
python frontend/data_preparation/main.py
```

**Common Actions:**
- Export dataset: Select dataset → Click "💾 Export Dataset"
- Delete dataset: Select dataset → Click "🗑️ Delete Dataset"
- View statistics: Click "📊 Statistics" toolbar button
- Filter datasets: Click sidebar buttons (Processing/Completed/Failed)
- Browse exports: Click "📁 Exported Files" toolbar button

---

## Admin Frontend (`frontend/admin/app.py`)

### High-Priority Features
| Feature | Function | Location | Description |
|---------|----------|----------|-------------|
| **Service Control** | `start_all_services()`, etc. | Lines ~380 | Bulk start/stop/restart for all backends |

### Medium-Priority Features
| Feature | Function | Location | Description |
|---------|----------|----------|-------------|
| **Database Management** | `show_database()` | Lines ~680 | UDS3 backend status + connection tests |
| **Config Manager** | `show_configuration()` | Lines ~930 | System-wide config editor with validation |

### Usage
```bash
# Start Admin Frontend
python frontend/admin/main.py
```

**Common Actions:**
- Control services: Use toolbar buttons (▶️ Start / ⏸️ Stop / 🔄 Restart)
- Check databases: Click "🗄️ Database" sidebar → Test connections
- Edit configs: Click "⚙️ Configuration" sidebar → Select file → Edit

---

## Feature Comparison Matrix

| Feature Category | Training | Data Prep | Admin |
|-----------------|----------|-----------|-------|
| **Job Management** | ✅ Cancel, Metrics | - | - |
| **Dataset Management** | - | ✅ Export, Delete, Stats | - |
| **Service Control** | ✅ Single service | - | ✅ All services |
| **Configuration** | ✅ Training configs | - | ✅ System configs |
| **File Browsers** | ✅ Model outputs | ✅ Exports | - |
| **Monitoring** | ✅ Workers, Metrics | ✅ Statistics | ✅ Databases |

---

## Common Workflows

### Workflow 1: Train Model → Monitor → Export
```
1. Training Frontend: Create training job
2. Training Frontend: View job metrics (📊)
3. Training Frontend: Monitor worker status
4. Training Frontend: Browse output files (📁)
5. Training Frontend: Open model in Explorer
```

### Workflow 2: Prepare Dataset → Export → Verify
```
1. Data Prep Frontend: Create dataset
2. Data Prep Frontend: View statistics (📊)
3. Data Prep Frontend: Export dataset (💾)
4. Data Prep Frontend: Browse exported files (📁)
5. Data Prep Frontend: Open export location
```

### Workflow 3: System Administration
```
1. Admin Frontend: Check database status (🗄️)
2. Admin Frontend: Test all connections
3. Admin Frontend: Edit system config (⚙️)
4. Admin Frontend: Restart services (🔄)
5. Admin Frontend: Monitor service health
```

---

## Keyboard Shortcuts

### Global (All Frontends)
- **F5:** Refresh current view
- **Ctrl+L:** Clear logs
- **Escape:** Close current dialog

### Training Frontend
- **Ctrl+M:** View job metrics
- **Ctrl+K:** Cancel selected job
- **Ctrl+O:** Open config manager

### Data Preparation Frontend
- **Ctrl+E:** Export selected dataset
- **Delete:** Delete selected dataset
- **Ctrl+S:** View statistics

### Admin Frontend
- **Ctrl+D:** Open database management
- **Ctrl+Shift+S:** Start all services
- **Ctrl+Shift+X:** Stop all services

---

## Troubleshooting

### Issue: Feature Not Working
**Solution:**
1. Check backend is running (`http://localhost:45678/health`)
2. Verify API connection in status bar
3. Check logs in bottom panel
4. Restart frontend application

### Issue: Config Validation Fails
**Solution:**
1. Click "✅ Validate" to see error details
2. Fix YAML syntax (indentation, colons)
3. Use "🔄 Reload" to discard changes
4. Backup file saved as `.bak` - restore if needed

### Issue: File Browser Empty
**Solution:**
1. Click "🔄 Refresh" button
2. Verify directory exists (models/ or data/exports/)
3. Check file permissions
4. Look for error in log panel

### Issue: Connection Test Fails
**Solution:**
1. Verify backend is running
2. Check host/port in config
3. Test with: `Test-NetConnection -ComputerName 192.168.178.94 -Port 5432`
4. Review firewall settings

---

## API Endpoints Used

### Training Backend (Port 45678)
- `GET /health` - Health check
- `GET /api/jobs` - List jobs
- `POST /api/jobs/{id}/cancel` - Cancel job
- `GET /api/jobs/{id}/metrics` - Job metrics
- `GET /workers/status` - Worker pool status

### Dataset Backend (Port 45679)
- `GET /health` - Health check
- `GET /api/datasets` - List datasets
- `POST /api/datasets/{id}/export` - Export dataset
- `DELETE /api/datasets/{id}` - Delete dataset
- `GET /api/datasets/{id}/statistics` - Dataset stats

---

## File Locations

### Configuration Files
- **Training Configs:** `configs/*.yaml`
- **Backend Configs:** `backend/*.yaml`
- **Shared Configs:** `shared/*.yaml`

### Data Directories
- **Models:** `models/` (training outputs)
- **Exports:** `data/exports/` (dataset exports)
- **Backups:** `*.bak` files (config backups)

### Frontend Source
- **Training:** `frontend/training/app.py` (1,670 lines)
- **Data Prep:** `frontend/data_preparation/app.py` (1,580 lines)
- **Admin:** `frontend/admin/app.py` (1,230 lines)

---

## Dependencies

### Python Packages
```python
# UI Framework
tkinter
ttk

# File Operations
pathlib
shutil

# Data Handling
json
yaml  # Optional, with fallback

# Networking
socket
requests

# Plotting
matplotlib

# Date/Time
datetime

# Threading
threading
subprocess
```

### Installation
```bash
# Install required packages
pip install matplotlib pyyaml requests

# All other dependencies are Python standard library
```

---

## Testing

### Quick Test Commands
```bash
# Test imports
python -c "from frontend.training.app import TrainingFrontend"
python -c "from frontend.data_preparation.app import DataPreparationFrontend"
python -c "from frontend.admin.app import AdminFrontend"

# Test backend connectivity
curl http://localhost:45678/health
curl http://localhost:45679/health
```

### Manual Testing Checklist
- [ ] Training Frontend: Cancel job
- [ ] Training Frontend: View metrics
- [ ] Training Frontend: Browse output files
- [ ] Data Prep Frontend: Export dataset
- [ ] Data Prep Frontend: Delete dataset
- [ ] Data Prep Frontend: View statistics
- [ ] Admin Frontend: Test database connections
- [ ] Admin Frontend: Edit configuration
- [ ] Admin Frontend: Start/stop services

---

## Performance Notes

### Recommended Limits
- **File Browser:** Max 1,000 files per directory
- **Metrics Charts:** Max 10,000 data points
- **Statistics:** Max 100,000 documents
- **Connection Test:** 2-second timeout

### Optimization Tips
1. Use filtering to reduce displayed items
2. Refresh only when needed (not auto-refresh)
3. Close unused windows to free memory
4. Clear logs periodically (Ctrl+L)

---

## Support

### Documentation
- 📄 [High-Priority Implementation](HIGH_PRIORITY_FEATURES_IMPLEMENTATION.md)
- 📄 [Medium-Priority Implementation](MEDIUM_PRIORITY_FEATURES_IMPLEMENTATION.md)
- 📄 [Frontend Analysis](FRONTEND_FUNCTIONS_ANALYSIS.md)

### Code Examples
See implementation reports for detailed code examples and patterns.

### Common Patterns
- **Error Handling:** All features use try/except with messageboxes
- **File Operations:** PathLib with backup creation
- **Validation:** YAML/JSON syntax checking before save
- **Threading:** Background workers for long operations

---

**Last Updated:** 25. Oktober 2025  
**Version:** 1.0.0  
**Status:** ✅ Production Ready
