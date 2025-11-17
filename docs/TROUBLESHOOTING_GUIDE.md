# CLARA AI - Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2025-11-17  
**Status:** Production

## Overview

This guide provides solutions to common issues encountered when deploying, configuring, or using the CLARA AI system. Issues are organized by category for quick reference.

## Quick Diagnostic Commands

```bash
# Check backend health
curl http://localhost:45680/health
curl http://localhost:45681/health

# Check service status (Linux)
systemctl status clara-training
systemctl status clara-dataset

# Check service status (Windows PowerShell)
Get-Process -Name python | Where-Object {$_.Path -like "*backend*"}

# Check logs (Linux systemd)
journalctl -u clara-training -n 100 --no-pager
journalctl -u clara-dataset -n 100 --no-pager

# Check logs (Docker)
docker logs clara-training-backend
docker logs clara-dataset-backend

# Check database connection
psql -h 192.168.178.94 -p 5432 -U postgres -d postgres -c "SELECT 1"

# Test JWT token generation
python -c "from shared.auth.jwt_auth import generate_token; print(generate_token({'sub': 'test', 'role': 'admin'}))"
```

---

## 1. Backend Connection Issues

### Issue 1.1: "Connection refused" when accessing backends

**Symptoms:**
```
requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionRefusedError(10061, 'No connection could be made because the target machine actively refused it'))
```

**Possible Causes:**
1. Backend not running
2. Wrong port in configuration
3. Firewall blocking connection
4. Backend crashed on startup

**Solutions:**

**Check if backend is running:**
```bash
# Windows
netstat -ano | findstr "45680"
netstat -ano | findstr "45681"

# Linux/macOS
lsof -i :45680
lsof -i :45681
```

**Start backends manually:**
```bash
# Training Backend
python -m backend.training.app

# Dataset Backend
python -m backend.datasets.app
```

**Check configuration:**
```python
from config import config
print(f"Training port: {config.training_port}")
print(f"Dataset port: {config.dataset_port}")
```

**Check firewall (Windows):**
```powershell
# Allow ports through firewall
New-NetFirewallRule -DisplayName "CLARA Training Backend" -Direction Inbound -LocalPort 45680 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "CLARA Dataset Backend" -Direction Inbound -LocalPort 45681 -Protocol TCP -Action Allow
```

**Check firewall (Linux):**
```bash
# UFW
sudo ufw allow 45680/tcp
sudo ufw allow 45681/tcp

# firewalld
sudo firewall-cmd --add-port=45680/tcp --permanent
sudo firewall-cmd --add-port=45681/tcp --permanent
sudo firewall-cmd --reload
```

---

### Issue 1.2: Backend starts but immediately crashes

**Symptoms:**
- Backend process exits immediately after starting
- Error messages about missing modules or configuration

**Common Errors:**

**Missing dependencies:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Verify virtual environment is activated
python -c "import sys; print(sys.prefix)"

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep uvicorn
```

**Configuration file missing:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'config/training.yaml'
```

**Solution:**
```bash
# Create config directory if missing
mkdir -p config

# Copy example configs
cp config/training.example.yaml config/training.yaml
cp config/dataset.example.yaml config/dataset.yaml

# Or use environment variables
export CLARA_TRAINING_PORT=45680
export CLARA_DATASET_PORT=45681
```

**Port already in use:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process using port (Linux/macOS)
lsof -i :45680
kill -9 <PID>

# Find process using port (Windows)
netstat -ano | findstr "45680"
taskkill /PID <PID> /F

# Or change port in configuration
export CLARA_TRAINING_PORT=45690
```

---

## 2. Database Issues

### Issue 2.1: PostgreSQL connection failed

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solutions:**

**Check PostgreSQL is running:**
```bash
# Linux
systemctl status postgresql

# Windows
Get-Service -Name postgresql*

# Docker
docker ps | grep postgres
```

**Verify connection parameters:**
```python
from config import config
print(f"PostgreSQL host: {config.postgres_host}")
print(f"PostgreSQL port: {config.postgres_port}")
print(f"PostgreSQL database: {config.postgres_database}")
```

**Test connection manually:**
```bash
psql -h 192.168.178.94 -p 5432 -U postgres -d postgres
```

**Check pg_hba.conf (if authentication fails):**
```bash
# Location: /etc/postgresql/*/main/pg_hba.conf
# Add line:
host    all             all             0.0.0.0/0               md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

**Check postgresql.conf (if remote connection fails):**
```bash
# Location: /etc/postgresql/*/main/postgresql.conf
# Set:
listen_addresses = '*'

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

### Issue 2.2: UDS3 databases not available

**Symptoms:**
```
WARNING: UDS3 not available. Advanced search features disabled.
```

**Understanding:**
- UDS3 is **OPTIONAL** - system works without it
- Only advanced hybrid search requires UDS3
- Basic dataset operations work without UDS3

**Check UDS3 availability:**
```python
from shared.database.dataset_search import UDS3_AVAILABLE
print(f"UDS3 available: {UDS3_AVAILABLE}")
```

**To enable UDS3 (if needed):**

1. Install UDS3 package:
```bash
# Install from external repository
pip install uds3
```

2. Start UDS3 databases:
```bash
# ChromaDB
docker run -d -p 8000:8000 chromadb/chroma

# Neo4j
docker run -d -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest

# Verify connections
curl http://localhost:8000/api/v1/heartbeat
curl http://localhost:7474
```

3. Configure UDS3:
```bash
export UDS3_CHROMA_HOST=localhost
export UDS3_CHROMA_PORT=8000
export UDS3_NEO4J_URI=bolt://localhost:7687
export UDS3_NEO4J_USER=neo4j
export UDS3_NEO4J_PASSWORD=password
```

**Reference:** See `docs/UDS3_STATUS.md` for complete details.

---

## 3. Authentication Issues

### Issue 3.1: JWT token validation failed

**Symptoms:**
```
401 Unauthorized: Invalid or expired token
```

**Solutions:**

**Check security mode:**
```python
from config import config
print(f"Security mode: {config.security_mode}")
```

**Security modes:**
- `development` - No auth required (local dev only)
- `jwt_optional` - Auth optional, accepts valid tokens
- `jwt_required` - Auth required, rejects missing tokens
- `production` - Full JWT + RBAC enforcement

**Generate valid token:**
```python
from shared.auth.jwt_auth import generate_token

# Admin token
token = generate_token({
    'sub': 'user@example.com',
    'role': 'admin',
    'permissions': ['read', 'write', 'admin']
})
print(f"Token: {token}")
```

**Use token in requests:**
```bash
# cURL
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:45680/api/training/jobs

# Python
import requests
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:45680/api/training/jobs", headers=headers)
```

**Check token expiration:**
```python
import jwt
from config import config

try:
    decoded = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
    print(f"Token valid until: {decoded['exp']}")
except jwt.ExpiredSignatureError:
    print("Token expired - generate new token")
except jwt.InvalidTokenError as e:
    print(f"Invalid token: {e}")
```

---

### Issue 3.2: RBAC permission denied

**Symptoms:**
```
403 Forbidden: Insufficient permissions
```

**Solution:**

**Check user role and permissions:**
```python
decoded_token = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
print(f"User role: {decoded_token.get('role')}")
print(f"Permissions: {decoded_token.get('permissions')}")
```

**Role permission requirements:**

| Role | Permissions | Can Do |
|------|-------------|--------|
| `admin` | `['read', 'write', 'admin']` | Everything |
| `trainer` | `['read', 'write']` | Create/manage training jobs |
| `analyst` | `['read', 'write']` | Create/manage datasets |
| `viewer` | `['read']` | View jobs and datasets only |

**Generate token with correct role:**
```python
# Admin token
admin_token = generate_token({
    'sub': 'admin@example.com',
    'role': 'admin',
    'permissions': ['read', 'write', 'admin']
})

# Trainer token
trainer_token = generate_token({
    'sub': 'trainer@example.com',
    'role': 'trainer',
    'permissions': ['read', 'write']
})
```

---

## 4. Training Job Issues

### Issue 4.1: Training job stuck in "queued" status

**Symptoms:**
- Job created successfully but never starts
- Status remains "queued" indefinitely

**Possible Causes:**
1. Worker pool exhausted (all workers busy)
2. Resource constraints (CPU/memory)
3. Missing model files
4. Configuration error

**Solutions:**

**Check worker pool status:**
```python
import requests
response = requests.get("http://localhost:45680/api/training/jobs/list?status=running")
running_jobs = response.json()
print(f"Running jobs: {len(running_jobs)}")
print(f"Max concurrent jobs: {config.max_concurrent_jobs}")
```

**Check system resources:**
```bash
# CPU usage
top -b -n 1 | head -20

# Memory usage
free -h

# GPU usage (if applicable)
nvidia-smi
```

**Check job logs:**
```bash
# Linux systemd
journalctl -u clara-training -f

# Docker
docker logs -f clara-training-backend

# Look for errors like:
# - "No such file or directory: '/models/base_model.pt'"
# - "CUDA out of memory"
# - "Configuration validation error"
```

**Cancel stuck job and retry:**
```bash
# Cancel job
curl -X DELETE http://localhost:45680/api/training/jobs/{job_id}

# Retry with corrected configuration
curl -X POST http://localhost:45680/api/training/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "trainer_type": "lora",
    "config_path": "/data/configs/lora_config.yaml",
    "dataset_path": "/data/datasets/training_data.jsonl",
    "priority": 5
  }'
```

---

### Issue 4.2: Training job failed with error

**Symptoms:**
- Job status changed to "failed"
- Error message in job details

**Common Errors:**

**Dataset format error:**
```
ValueError: Invalid JSONL format in training dataset
```

**Solution:**
```bash
# Validate JSONL format
python -c "
import json
with open('training_data.jsonl') as f:
    for i, line in enumerate(f, 1):
        try:
            json.loads(line)
        except json.JSONDecodeError as e:
            print(f'Line {i}: {e}')
"

# Expected format:
# {"text": "Sample text", "label": "category"}
# {"text": "Another sample", "label": "category2"}
```

**Model file not found:**
```
FileNotFoundError: Base model not found at /models/base_model.pt
```

**Solution:**
```bash
# Check model path in config
cat config/training.yaml | grep model_path

# Download model if missing
mkdir -p /models
# Download from Hugging Face or other source

# Or update config to correct path
sed -i 's|/models/base_model.pt|/path/to/actual/model.pt|g' config/training.yaml
```

**Out of memory:**
```
RuntimeError: CUDA out of memory
```

**Solution:**
```yaml
# Reduce batch size in training config
training:
  batch_size: 4  # Reduce from 16 to 4
  gradient_accumulation_steps: 4  # Increase to maintain effective batch size
```

---

## 5. Dataset Management Issues

### Issue 5.1: Dataset export stuck

**Symptoms:**
- Dataset export request returns 202 Accepted
- Export never completes

**Solutions:**

**Check export job status:**
```python
import requests
response = requests.get(f"http://localhost:45681/api/datasets/{dataset_id}")
dataset = response.json()
print(f"Status: {dataset['status']}")
print(f"Export formats: {dataset.get('exported_formats', [])}")
```

**Check backend logs:**
```bash
# Look for export-related errors
journalctl -u clara-dataset -n 100 --no-pager | grep -i export
```

**Common issues:**
- Disk space full (check with `df -h`)
- Write permission error (check directory permissions)
- Export format not supported

**Retry export:**
```bash
# Delete failed export files
rm -rf /data/exports/{dataset_id}/

# Retry export
curl -X POST http://localhost:45681/api/datasets/{dataset_id}/export \
  -H "Content-Type: application/json" \
  -d '{"formats": ["jsonl", "parquet"]}'
```

---

### Issue 5.2: Dataset search returns no results

**Symptoms:**
- Search query returns empty results
- Expected documents not found

**Solutions:**

**Check if UDS3 is available (for advanced search):**
```python
from shared.database.dataset_search import UDS3_AVAILABLE
print(f"UDS3 available: {UDS3_AVAILABLE}")
```

**If UDS3 not available:**
- Only basic dataset listing works
- Advanced hybrid search disabled
- See Issue 2.2 to enable UDS3

**If UDS3 available:**

**Check search query syntax:**
```bash
# Correct query format
curl -X GET "http://localhost:45681/api/datasets?query=compliance+AND+regulation"

# Check database has documents
psql -h 192.168.178.94 -U postgres -d postgres -c "SELECT COUNT(*) FROM documents;"
```

**Rebuild search indices (if needed):**
```python
# This would require UDS3 admin scripts
# Contact system administrator
```

---

## 6. Configuration Issues

### Issue 6.1: Environment variables not loaded

**Symptoms:**
- Configuration uses default values instead of custom values
- Environment variables set but not used

**Solutions:**

**Check environment variable naming:**
```bash
# Correct format: CLARA_ prefix
export CLARA_TRAINING_PORT=45690
export CLARA_DATASET_PORT=45691
export CLARA_SECURITY_MODE=production

# Wrong (will be ignored):
export TRAINING_PORT=45690  # Missing CLARA_ prefix
```

**Check environment file loading:**
```bash
# Verify .env file exists
ls -la .env*

# Load manually
export $(cat .env | xargs)

# Verify loaded
printenv | grep CLARA
```

**Check configuration hierarchy:**
1. Hardcoded defaults (lowest priority)
2. Config files (config/training.yaml, config/dataset.yaml)
3. Environment variables (highest priority)

**Test configuration:**
```python
from config import config
print(f"Training port: {config.training_port} (expected: {os.getenv('CLARA_TRAINING_PORT')})")
```

**Reference:** See `docs/CONFIGURATION_REFERENCE.md` for complete details.

---

### Issue 6.2: Config file syntax error

**Symptoms:**
```
yaml.scanner.ScannerError: while scanning for the next token
```

**Solution:**

**Validate YAML syntax:**
```bash
# Install yamllint
pip install yamllint

# Check syntax
yamllint config/training.yaml
yamllint config/dataset.yaml
```

**Common YAML errors:**
```yaml
# Wrong (missing space after colon)
training_port:45680

# Correct
training_port: 45680

# Wrong (inconsistent indentation)
training:
  batch_size: 16
   epochs: 10  # Extra space

# Correct
training:
  batch_size: 16
  epochs: 10
```

**Use example config as reference:**
```bash
cp config/training.example.yaml config/training.yaml
# Edit carefully
```

---

## 7. Performance Issues

### Issue 7.1: Slow API response times

**Symptoms:**
- API requests take >5 seconds
- Timeout errors

**Solutions:**

**Check system resources:**
```bash
# CPU usage
top

# Memory usage
free -h

# Disk I/O
iostat -x 1
```

**Check database query performance:**
```sql
-- Enable query logging in PostgreSQL
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- Log queries >1s
SELECT pg_reload_conf();

-- View slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

**Add database indices (if missing):**
```sql
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON training_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON training_jobs(created_at);
```

**Check worker pool configuration:**
```python
from config import config
print(f"Max concurrent jobs: {config.max_concurrent_jobs}")
print(f"Worker threads: {config.worker_threads}")

# Increase if resources available
export CLARA_MAX_CONCURRENT_JOBS=10
export CLARA_WORKER_THREADS=8
```

**Enable caching (if applicable):**
```python
# Add to backend configuration
CACHE_ENABLED = True
CACHE_TTL = 300  # 5 minutes
```

---

### Issue 7.2: High memory usage

**Symptoms:**
- Backend consuming >4GB RAM
- Out of memory errors

**Solutions:**

**Check memory usage:**
```bash
# Current memory usage
ps aux | grep python | awk '{print $6/1024 " MB  " $11}'

# Monitor over time
watch -n 5 "ps aux | grep python | awk '{print \$6/1024 \" MB  \" \$11}'"
```

**Reduce memory footprint:**

1. **Reduce worker count:**
```python
export CLARA_MAX_CONCURRENT_JOBS=2  # Reduce from 5
export CLARA_WORKER_THREADS=4  # Reduce from 8
```

2. **Enable garbage collection:**
```python
import gc
gc.set_threshold(700, 10, 10)  # More aggressive GC
```

3. **Limit batch sizes:**
```yaml
# In training config
training:
  batch_size: 4  # Reduce from 16
  max_dataset_size: 10000  # Limit dataset size
```

4. **Use Docker memory limits:**
```yaml
services:
  training-backend:
    mem_limit: 2g
    mem_reservation: 1g
```

---

## 8. Docker Deployment Issues

### Issue 8.1: Docker container won't start

**Symptoms:**
```
docker: Error response from daemon: failed to create shim task
```

**Solutions:**

**Check Docker daemon:**
```bash
# Linux
sudo systemctl status docker

# Windows
Get-Service -Name com.docker.service
```

**Check Dockerfile syntax:**
```bash
# Validate Dockerfile
docker build --no-cache -t clara-test .

# Check for common errors:
# - Missing base image
# - Invalid COPY paths
# - Missing required files
```

**Check docker-compose.yml:**
```bash
# Validate syntax
docker-compose config

# Check for common errors:
# - Invalid service names
# - Missing environment variables
# - Invalid port mappings
```

**Check resource limits:**
```bash
# Increase Docker memory (Docker Desktop)
# Settings > Resources > Memory: 4GB minimum

# Check current limits
docker stats
```

---

### Issue 8.2: Docker containers can't communicate

**Symptoms:**
- Backend can't connect to database
- "Connection refused" errors between containers

**Solutions:**

**Check Docker network:**
```bash
# List networks
docker network ls

# Inspect network
docker network inspect clara-network

# Verify containers are on same network
docker inspect clara-training-backend | grep NetworkMode
docker inspect postgres | grep NetworkMode
```

**Use service names (not localhost):**
```yaml
# Wrong (in Docker container)
POSTGRES_HOST: localhost

# Correct (use service name)
POSTGRES_HOST: postgres
```

**Check port mappings:**
```bash
# List container ports
docker ps --format "table {{.Names}}\t{{.Ports}}"

# Should show:
# training-backend  0.0.0.0:45680->45680/tcp
# dataset-backend   0.0.0.0:45681->45681/tcp
# postgres          5432/tcp
```

**Test connectivity:**
```bash
# From host
curl http://localhost:45680/health

# From inside container
docker exec clara-training-backend curl http://postgres:5432
```

---

## 9. Frontend Issues

### Issue 9.1: Frontend can't connect to backend

**Symptoms:**
- "Backend not available" error in frontend
- Connection timeout in GUI

**Solutions:**

**Check backend URLs in frontend config:**
```python
# In frontend code
TRAINING_BACKEND_URL = "http://localhost:45680"
DATASET_BACKEND_URL = "http://localhost:45681"
```

**Test backend accessibility:**
```bash
# From same machine as frontend
curl http://localhost:45680/health
curl http://localhost:45681/health
```

**Check firewall (if frontend on different machine):**
```bash
# Allow backend access from other machines
# On backend machine (Linux):
sudo ufw allow from 192.168.1.0/24 to any port 45680
sudo ufw allow from 192.168.1.0/24 to any port 45681
```

**Use correct backend IP:**
```python
# If frontend on different machine, use backend IP
TRAINING_BACKEND_URL = "http://192.168.1.100:45680"
```

---

### Issue 9.2: Frontend GUI freezes

**Symptoms:**
- GUI becomes unresponsive
- "Not Responding" in task manager

**Solutions:**

**Check for long-running operations on main thread:**
```python
# Wrong (blocks GUI)
def on_button_click():
    result = requests.get(backend_url)  # Blocks GUI

# Correct (use threading)
import threading

def on_button_click():
    thread = threading.Thread(target=fetch_data)
    thread.daemon = True
    thread.start()

def fetch_data():
    result = requests.get(backend_url)
    # Update GUI using after()
    root.after(0, update_gui, result)
```

**Add timeouts to backend calls:**
```python
# Add timeout to prevent indefinite hanging
try:
    response = requests.get(backend_url, timeout=5)
except requests.Timeout:
    messagebox.showerror("Error", "Backend request timed out")
```

**Enable GUI refresh:**
```python
# Process GUI events during long operations
def long_operation():
    for i in range(100):
        # Do work
        root.update()  # Process GUI events
```

---

## 10. Logging and Diagnostics

### Enabling Debug Logging

**Backend debug logging:**
```python
# Set in environment or config
export CLARA_LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

**View logs:**
```bash
# Linux systemd
journalctl -u clara-training -f --no-pager

# Docker
docker logs -f clara-training-backend

# File logs (if configured)
tail -f /var/log/clara/training.log
```

### Health Check Script

```python
#!/usr/bin/env python3
"""CLARA System Health Check"""

import requests
import sys

def check_backend(name, url):
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ {name}: {e}")
        return False

def main():
    print("CLARA System Health Check\n")
    
    training_ok = check_backend("Training Backend", "http://localhost:45680")
    dataset_ok = check_backend("Dataset Backend", "http://localhost:45681")
    
    if training_ok and dataset_ok:
        print("\n✅ All systems operational")
        sys.exit(0)
    else:
        print("\n❌ Some systems are down")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## Getting Help

If you encounter an issue not covered in this guide:

1. **Check logs** - Most issues show error messages in logs
2. **Review documentation:**
   - `docs/DEPLOYMENT_GUIDE.md` - Deployment issues
   - `docs/API_REFERENCE.md` - API usage issues
   - `docs/CONFIGURATION_REFERENCE.md` - Configuration issues
   - `docs/TESTING_GUIDE.md` - Testing issues
3. **Search existing issues** - GitHub Issues (if applicable)
4. **Create support ticket** - With logs and error messages
5. **Contact system administrator** - For infrastructure issues

## Appendix: Common Error Codes

| HTTP Code | Meaning | Common Cause | Solution |
|-----------|---------|--------------|----------|
| 400 | Bad Request | Invalid request body | Check request format |
| 401 | Unauthorized | Missing/invalid JWT token | Generate valid token |
| 403 | Forbidden | Insufficient permissions | Check user role |
| 404 | Not Found | Resource doesn't exist | Check resource ID |
| 500 | Internal Server Error | Backend error | Check logs |
| 502 | Bad Gateway | Backend not reachable | Check backend status |
| 503 | Service Unavailable | Backend overloaded | Check resources |

## Quick Reference: Diagnostic Flow

```
Issue encountered
    ↓
1. Check logs (systemd/Docker)
    ↓
2. Run health check script
    ↓
3. Test backend connectivity
    ↓
4. Check configuration
    ↓
5. Verify database connection
    ↓
6. Check system resources
    ↓
7. Review relevant docs section
    ↓
8. Contact support if unresolved
```

---

**Document Maintenance:**
- Review quarterly for new issues
- Update with solutions to recurring problems
- Add examples from real support tickets
