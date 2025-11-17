# Configuration Reference

**Created:** 2025-11-17  
**Purpose:** Comprehensive reference for all CLARA configuration options  
**Status:** 🟢 ACTIVE

---

## Overview

CLARA uses a centralized configuration system based on **Pydantic Settings** with environment variable support. All configuration is managed through the `config` module with environment-specific overrides.

**Configuration Files:**
- `config/base.py` - Base configuration class with defaults
- `config/development.py` - Development environment overrides
- `config/production.py` - Production environment overrides
- `config/testing.py` - Testing environment overrides
- `config/__init__.py` - Configuration loader

---

## Environment Selection

The active configuration is determined by the `CLARA_ENVIRONMENT` variable:

```bash
# Development (default)
export CLARA_ENVIRONMENT=development

# Production
export CLARA_ENVIRONMENT=production

# Testing
export CLARA_ENVIRONMENT=testing
```

---

## Backend Service Ports

### Training Backend Port

**Config Variable:** `training_port`  
**Environment Variable:** `CLARA_TRAINING_PORT`  
**Default Value:** `45680`  
**Type:** Integer

**Usage in Code:**
```python
from config import config

# Access training port
port = config.training_port  # 45680 (default)
```

**Override via Environment:**
```bash
# PowerShell
$env:CLARA_TRAINING_PORT = "8080"

# Bash
export CLARA_TRAINING_PORT=8080
```

**Service Start:**
```bash
# Uses config.training_port
python -m backend.training.app

# Override at runtime
CLARA_TRAINING_PORT=8080 python -m backend.training.app
```

---

### Dataset Backend Port

**Config Variable:** `dataset_port`  
**Environment Variable:** `CLARA_DATASET_PORT`  
**Default Value:** `45681`  
**Type:** Integer

**Usage in Code:**
```python
from config import config

# Access dataset port
port = config.dataset_port  # 45681 (default)
```

**Override via Environment:**
```bash
# PowerShell
$env:CLARA_DATASET_PORT = "8081"

# Bash
export CLARA_DATASET_PORT=8081
```

**Service Start:**
```bash
# Uses config.dataset_port
python -m backend.datasets.app

# Override at runtime
CLARA_DATASET_PORT=8081 python -m backend.datasets.app
```

---

## Port Reference Table

| Service | Config Variable | Env Variable | Default | Override Example |
|---------|----------------|--------------|---------|------------------|
| Training Backend | `config.training_port` | `CLARA_TRAINING_PORT` | 45680 | `export CLARA_TRAINING_PORT=8080` |
| Dataset Backend | `config.dataset_port` | `CLARA_DATASET_PORT` | 45681 | `export CLARA_DATASET_PORT=8081` |

---

## Complete Configuration Reference

### Application Settings

| Variable | Env Variable | Default | Type | Description |
|----------|--------------|---------|------|-------------|
| `app_name` | `CLARA_APP_NAME` | "Clara Training System" | string | Application name |
| `environment` | `CLARA_ENVIRONMENT` | "development" | enum | Environment mode |
| `debug` | `CLARA_DEBUG` | `false` | boolean | Debug mode |
| `log_level` | `CLARA_LOG_LEVEL` | "INFO" | string | Logging level |

### API Settings

| Variable | Env Variable | Default | Type | Description |
|----------|--------------|---------|------|-------------|
| `api_host` | `CLARA_API_HOST` | "0.0.0.0" | string | API bind address |
| `api_port` | `CLARA_API_PORT` | 8000 | integer | API port (main app) |
| `api_workers` | `CLARA_API_WORKERS` | 4 | integer | Number of workers |
| `api_reload` | `CLARA_API_RELOAD` | `false` | boolean | Auto-reload on changes |

### Backend Service Ports

| Variable | Env Variable | Default | Type | Description |
|----------|--------------|---------|------|-------------|
| `training_port` | `CLARA_TRAINING_PORT` | 45680 | integer | Training backend port |
| `dataset_port` | `CLARA_DATASET_PORT` | 45681 | integer | Dataset backend port |

### Worker Configuration

| Variable | Env Variable | Default | Type | Description |
|----------|--------------|---------|------|-------------|
| `max_concurrent_jobs` | `CLARA_MAX_CONCURRENT_JOBS` | 2 | integer | Max parallel training jobs |
| `worker_timeout` | `CLARA_WORKER_TIMEOUT` | 3600 | integer | Worker timeout (seconds) |

### Security Settings

| Variable | Env Variable | Default | Type | Description |
|----------|--------------|---------|------|-------------|
| `security_mode` | `CLARA_SECURITY_MODE` | "production" | enum | Security mode (production/development/debug/testing) |
| `jwt_enabled` | `CLARA_JWT_ENABLED` | `null` | boolean? | Enable JWT (auto-determined by security_mode if null) |
| `mtls_enabled` | `CLARA_MTLS_ENABLED` | `null` | boolean? | Enable mTLS (auto-determined by security_mode if null) |

### Keycloak Settings

| Variable | Env Variable | Default | Type | Description |
|----------|--------------|---------|------|-------------|
| `keycloak_url` | `KEYCLOAK_URL` | "http://localhost:8080" | string | Keycloak server URL |
| `keycloak_realm` | `KEYCLOAK_REALM` | "vcc" | string | Keycloak realm name |
| `keycloak_client_id` | `KEYCLOAK_CLIENT_ID` | "clara-training-system" | string | OAuth2 client ID |

### Training Configuration

| Variable | Env Variable | Default | Type | Description |
|----------|--------------|---------|------|-------------|
| `training_output_dir` | `CLARA_TRAINING_OUTPUT_DIR` | "models/" | Path | Output directory for models |
| `dataset_cache_dir` | `CLARA_DATASET_CACHE_DIR` | "data/cache/" | Path | Dataset cache directory |
| `checkpoint_dir` | `CLARA_CHECKPOINT_DIR` | "checkpoints/" | Path | Training checkpoint directory |

---

## Configuration Hierarchy

Configuration values are loaded in the following order (later overrides earlier):

1. **Base Defaults** (`config/base.py`)
2. **Environment Config** (`config/development.py`, `config/production.py`, or `config/testing.py`)
3. **Environment Variables** (e.g., `CLARA_TRAINING_PORT=8080`)
4. **Command-line Arguments** (if implemented by specific script)

---

## Examples

### Example 1: Custom Ports for Development

```bash
# PowerShell
$env:CLARA_ENVIRONMENT = "development"
$env:CLARA_TRAINING_PORT = "8080"
$env:CLARA_DATASET_PORT = "8081"

# Start services
python -m backend.training.app  # Runs on port 8080
python -m backend.datasets.app  # Runs on port 8081
```

### Example 2: Production Configuration

```bash
# Bash
export CLARA_ENVIRONMENT=production
export CLARA_SECURITY_MODE=production
export CLARA_JWT_ENABLED=true
export CLARA_MTLS_ENABLED=true
export CLARA_TRAINING_PORT=45680
export CLARA_DATASET_PORT=45681
export KEYCLOAK_URL=https://keycloak.example.com

# Start services
python -m backend.training.app
python -m backend.datasets.app
```

### Example 3: Testing with Mock Security

```bash
# Bash
export CLARA_ENVIRONMENT=testing
export CLARA_SECURITY_MODE=debug
export CLARA_JWT_ENABLED=false
export CLARA_TRAINING_PORT=45680
export CLARA_DATASET_PORT=45681

# Start services (no authentication required)
python -m backend.training.app
python -m backend.datasets.app
```

### Example 4: Accessing Configuration in Code

```python
from config import config

# Access configuration values
print(f"Environment: {config.environment}")
print(f"Training Port: {config.training_port}")
print(f"Dataset Port: {config.dataset_port}")
print(f"Security Mode: {config.security_mode}")
print(f"JWT Enabled: {config.jwt_enabled}")

# Use in FastAPI app
from fastapi import FastAPI
import uvicorn

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.api_host,
        port=config.training_port,  # Uses config value
        workers=config.api_workers
    )
```

---

## Environment Files

You can use `.env` files to store configuration (not committed to git):

```bash
# .env.development
CLARA_ENVIRONMENT=development
CLARA_DEBUG=true
CLARA_LOG_LEVEL=DEBUG
CLARA_TRAINING_PORT=8080
CLARA_DATASET_PORT=8081
CLARA_SECURITY_MODE=debug
CLARA_JWT_ENABLED=false

# .env.production
CLARA_ENVIRONMENT=production
CLARA_DEBUG=false
CLARA_LOG_LEVEL=INFO
CLARA_TRAINING_PORT=45680
CLARA_DATASET_PORT=45681
CLARA_SECURITY_MODE=production
CLARA_JWT_ENABLED=true
CLARA_MTLS_ENABLED=true
KEYCLOAK_URL=https://keycloak.production.example.com
```

**Load with:**
```bash
# PowerShell
Get-Content .env.development | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        Set-Item -Path "env:$($Matches[1])" -Value $Matches[2]
    }
}

# Bash
export $(cat .env.development | xargs)
```

---

## Port Conflict Resolution

If default ports (45680, 45681) are already in use:

### Check Port Usage

```bash
# Windows
netstat -ano | findstr :45680
netstat -ano | findstr :45681

# Linux/Mac
lsof -i :45680
lsof -i :45681
```

### Change Ports

**Option 1: Environment Variables**
```bash
export CLARA_TRAINING_PORT=8080
export CLARA_DATASET_PORT=8081
```

**Option 2: Update Config File**
```python
# config/development.py
from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    training_port: int = 8080  # Changed from 45680
    dataset_port: int = 8081   # Changed from 45681
```

---

## Best Practices

1. **Use Environment Variables** for deployment-specific values (ports, URLs, passwords)
2. **Keep .env files out of git** (add to `.gitignore`)
3. **Document required variables** for each environment
4. **Use defaults wisely** - defaults should work for development
5. **Validate configuration** at startup (Pydantic does this automatically)
6. **Never hardcode** ports or URLs in application code - always use `config.*`

---

## Troubleshooting

### "Port already in use"

**Cause:** Another service is using the default port

**Solution:**
```bash
# Find what's using the port
netstat -ano | findstr :45680  # Windows
lsof -i :45680                 # Linux/Mac

# Kill the process or change port
export CLARA_TRAINING_PORT=8080
```

### "Configuration not loading"

**Cause:** Environment variables not set

**Check:**
```bash
# PowerShell
$env:CLARA_ENVIRONMENT
$env:CLARA_TRAINING_PORT

# Bash
echo $CLARA_ENVIRONMENT
echo $CLARA_TRAINING_PORT
```

**Solution:** Set environment variables before starting services

### "Wrong port in logs"

**Cause:** Config cached or environment variable not visible

**Solution:**
```bash
# Verify environment variable is set
echo $CLARA_TRAINING_PORT

# Restart with explicit value
CLARA_TRAINING_PORT=8080 python -m backend.training.app
```

---

## Migration from Hardcoded Ports

### Old Way (Hardcoded)

```python
# ❌ Don't do this
app = FastAPI()
uvicorn.run(app, port=45680)  # Hardcoded port
```

### New Way (Config-based)

```python
# ✅ Do this
from config import config

app = FastAPI()
uvicorn.run(app, port=config.training_port)  # Uses config
```

### Updating Documentation

When documenting port numbers:
- ❌ **Don't write:** "Port 45680"
- ✅ **Do write:** "Port config.training_port (default: 45680)"

---

## Related Documentation

- **DOCUMENTATION_TODO.md** - Task 1.3 (Port Configuration Standardization)
- **GAP_ANALYSIS.md** - Port configuration gaps identified
- **config/base.py** - Source of truth for default values
- **DEPLOYMENT_GUIDE.md** - Production deployment configuration

---

**Last Updated:** 2025-11-17  
**Maintainer:** Documentation Team
