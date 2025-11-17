# CLARA AI System - Deployment Guide

**Complete deployment instructions for all environments**

---

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Development Setup](#development-setup)
4. [Production Deployment](#production-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Service Management](#service-management)
7. [Docker Deployment](#docker-deployment)
8. [Health Checks & Monitoring](#health-checks--monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Upgrade & Maintenance](#upgrade--maintenance)

---

## Overview

### Architecture

CLARA consists of 3 main components:

1. **Training Backend** (Port 45680) - Job management, training execution
2. **Dataset Backend** (Port 45681) - Dataset creation, export, UDS3 integration
3. **Frontend Applications** - 3 tkinter GUIs (Admin, Training, Data Prep)

### Deployment Modes

| Mode | Security | Use Case |
|------|----------|----------|
| **Development** | JWT Optional | Local dev, testing |
| **Production** | JWT + mTLS | Production deployment |
| **Debug** | No auth | Debugging only |
| **Testing** | Mock JWT | Automated tests |

---

## System Requirements

### Minimum Requirements

**Hardware:**
- CPU: 4 cores (Intel/AMD)
- RAM: 8 GB
- Disk: 50 GB free space
- GPU: NVIDIA GPU (optional, for training)

**Software:**
- OS: Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+
- Python: 3.8 or higher (3.10+ recommended)
- PowerShell: 5.1+ (Windows) or PowerShell Core 7+ (Linux/macOS)

### Recommended Requirements

**Hardware:**
- CPU: 8+ cores
- RAM: 16 GB+
- Disk: 200 GB+ SSD
- GPU: NVIDIA RTX 3060+ with 12GB+ VRAM

**Software:**
- Python: 3.10+
- CUDA Toolkit: 11.8+ (if using GPU)
- PostgreSQL: 14+
- Docker: 20.10+ (optional)

### Dependencies

**Core Dependencies:**
```
fastapi>=0.104.1          # Backend framework
uvicorn[standard]>=0.24.0 # ASGI server
pydantic>=2.5.0           # Data validation
torch>=2.0.0              # Deep learning framework
transformers>=4.30.0      # HuggingFace models
peft>=0.4.0               # LoRA/QLoRA training
```

**Optional Dependencies:**
```
uds3                      # Advanced search (external package)
vllm>=0.3.3               # High-performance inference
wandb>=0.15.0             # Experiment tracking
```

See `requirements.txt` for complete list.

---

## Development Setup

### 1. Clone Repository

```bash
# Clone repository
git clone https://github.com/yourusername/VCC-Clara.git
cd VCC-Clara
```

### 2. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install API-only dependencies (lightweight)
pip install -r requirements_api.txt
```

### 4. Configure Environment

```powershell
# Copy example environment file
cp .env.example .env.dev

# Edit configuration
notepad .env.dev  # Windows
nano .env.dev     # Linux/macOS
```

**Minimal Development Config (.env.dev):**
```bash
# Security (no auth for development)
CLARA_SECURITY_MODE=debug
CLARA_JWT_ENABLED=false

# Ports
CLARA_TRAINING_PORT=45680
CLARA_DATASET_PORT=45681

# Logging
LOG_LEVEL=DEBUG
ENABLE_API_DOCS=true
```

### 5. Start Services

**Windows (All-in-One):**
```powershell
.\start_clara.ps1
```

**Windows (Backends Only):**
```powershell
.\start_backends.ps1
```

**Linux/macOS:**
```bash
# Start Training Backend
python -m backend.training.app &

# Start Dataset Backend
python -m backend.datasets.app &

# Check health
curl http://localhost:45680/health
curl http://localhost:45681/health
```

### 6. Verify Installation

```powershell
# Health checks
curl http://localhost:45680/health
curl http://localhost:45681/health

# API documentation
# Open browser: http://localhost:45680/docs
# Open browser: http://localhost:45681/docs
```

**Expected Output:**
```json
{
  "status": "healthy",
  "service": "training-backend",
  "port": 45680,
  "active_jobs": 0,
  "timestamp": "2025-11-17T10:30:00Z"
}
```

---

## Production Deployment

### 1. System Preparation

**Update System:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3.10 python3-pip python3-venv postgresql-client
```

**Create Service User:**
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash clara
sudo usermod -aG sudo clara

# Switch to service user
sudo su - clara
```

### 2. Application Setup

```bash
# Clone repository
cd /opt
git clone https://github.com/yourusername/VCC-Clara.git
cd VCC-Clara

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Production Configuration

**Create Production Environment File (.env.prod):**
```bash
# ============================================================================
# PRODUCTION CONFIGURATION
# ============================================================================

# Security (FULL AUTHENTICATION)
CLARA_SECURITY_MODE=production
CLARA_JWT_ENABLED=true
CLARA_MTLS_ENABLED=true

# Keycloak Configuration
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=clara
KEYCLOAK_CLIENT_ID=clara-training-system
JWT_ALGORITHM=RS256

# Service Ports
CLARA_TRAINING_PORT=45680
CLARA_DATASET_PORT=45681

# Database Configuration
POSTGRES_HOST=db.your-domain.com
POSTGRES_PORT=5432
POSTGRES_USER=clara_prod
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DATABASE=clara_production

# Logging (Production Level)
LOG_LEVEL=WARNING
ENABLE_API_DOCS=false

# CORS (Specific Origins Only)
ENABLE_CORS=true
CORS_ORIGINS=https://clara.your-domain.com

# TLS Configuration
SERVICE_CERT_PATH=/etc/clara/certs/clara-training.crt
SERVICE_KEY_PATH=/etc/clara/certs/clara-training.key
CA_CERT_PATH=/etc/clara/certs/ca.crt

# Performance
TRAINING_IO_WORKERS=18
TRAINING_CPU_WORKERS=18
MAX_CONCURRENT_JOBS=10
```

### 4. Systemd Service Setup

**Training Backend Service (/etc/systemd/system/clara-training.service):**
```ini
[Unit]
Description=CLARA Training Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=clara
Group=clara
WorkingDirectory=/opt/VCC-Clara
Environment="PATH=/opt/VCC-Clara/venv/bin"
EnvironmentFile=/opt/VCC-Clara/.env.prod
ExecStart=/opt/VCC-Clara/venv/bin/python -m backend.training.app
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/VCC-Clara/data /opt/VCC-Clara/logs

[Install]
WantedBy=multi-user.target
```

**Dataset Backend Service (/etc/systemd/system/clara-dataset.service):**
```ini
[Unit]
Description=CLARA Dataset Backend Service
After=network.target postgresql.service

[Service]
Type=simple
User=clara
Group=clara
WorkingDirectory=/opt/VCC-Clara
Environment="PATH=/opt/VCC-Clara/venv/bin"
EnvironmentFile=/opt/VCC-Clara/.env.prod
ExecStart=/opt/VCC-Clara/venv/bin/python -m backend.datasets.app
Restart=always
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/VCC-Clara/data /opt/VCC-Clara/logs

[Install]
WantedBy=multi-user.target
```

**Enable and Start Services:**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable clara-training
sudo systemctl enable clara-dataset

# Start services
sudo systemctl start clara-training
sudo systemctl start clara-dataset

# Check status
sudo systemctl status clara-training
sudo systemctl status clara-dataset
```

### 5. Reverse Proxy Setup (Nginx)

**Nginx Configuration (/etc/nginx/sites-available/clara):**
```nginx
upstream training_backend {
    server 127.0.0.1:45680;
}

upstream dataset_backend {
    server 127.0.0.1:45681;
}

server {
    listen 80;
    server_name clara.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name clara.your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/clara.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clara.your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Training API
    location /api/training/ {
        proxy_pass http://training_backend/api/training/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Dataset API
    location /api/datasets/ {
        proxy_pass http://dataset_backend/api/datasets/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health checks
    location /health {
        access_log off;
        return 200 "healthy\n";
    }
}
```

**Enable Site:**
```bash
sudo ln -s /etc/nginx/sites-available/clara /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Environment Configuration

### Configuration Files

| File | Purpose |
|------|---------|
| `.env.dev` | Development (local) |
| `.env.prod` | Production |
| `.env.test` | Testing |
| `.env.example` | Template with all options |

### Configuration Hierarchy

1. **Environment Variables** (highest priority)
2. **`.env` file** (environment-specific)
3. **Default Values** (in code)

### Key Configuration Options

**Security:**
```bash
CLARA_SECURITY_MODE=production     # production | development | debug | testing
CLARA_JWT_ENABLED=true             # JWT authentication
CLARA_MTLS_ENABLED=true            # Mutual TLS
```

**Ports:**
```bash
CLARA_TRAINING_PORT=45680          # Training backend
CLARA_DATASET_PORT=45681           # Dataset backend
CLARA_SERVING_PORT=45682           # Model serving (future)
CLARA_METRICS_PORT=9310            # Prometheus metrics
```

**Database:**
```bash
POSTGRES_HOST=192.168.178.94
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
POSTGRES_DATABASE=postgres
```

**Performance:**
```bash
TRAINING_IO_WORKERS=18             # I/O worker pool size
TRAINING_CPU_WORKERS=18            # CPU worker pool size
MAX_CONCURRENT_JOBS=10             # Max parallel training jobs
JOB_TIMEOUT_SECONDS=3600           # Job timeout (1 hour)
```

**Logging:**
```bash
LOG_LEVEL=INFO                     # DEBUG | INFO | WARNING | ERROR
AUDIT_LOG_ENABLED=true             # Audit logging
METRICS_ENABLED=true               # Performance metrics
```

See [CONFIGURATION_REFERENCE.md](./CONFIGURATION_REFERENCE.md) for complete reference.

---

## Service Management

### Windows (PowerShell Scripts)

**Start All Services:**
```powershell
.\start_clara.ps1
```

**Start Backends Only:**
```powershell
.\start_backends.ps1
```

**Stop Services:**
```powershell
.\stop_backends.ps1
```

**Interactive Frontend Launcher:**
```powershell
.\launch_frontend.ps1
```

**Health Check:**
```powershell
# Check system status
python check_system_status.py

# Manual health checks
Invoke-RestMethod -Uri "http://localhost:45680/health"
Invoke-RestMethod -Uri "http://localhost:45681/health"
```

### Linux (Systemd)

**Service Control:**
```bash
# Start services
sudo systemctl start clara-training
sudo systemctl start clara-dataset

# Stop services
sudo systemctl stop clara-training
sudo systemctl stop clara-dataset

# Restart services
sudo systemctl restart clara-training
sudo systemctl restart clara-dataset

# Check status
sudo systemctl status clara-training
sudo systemctl status clara-dataset

# View logs
sudo journalctl -u clara-training -f
sudo journalctl -u clara-dataset -f
```

**Enable/Disable Auto-Start:**
```bash
# Enable (start on boot)
sudo systemctl enable clara-training
sudo systemctl enable clara-dataset

# Disable
sudo systemctl disable clara-training
sudo systemctl disable clara-dataset
```

---

## Docker Deployment

### Dockerfile (Training Backend)

```dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt

# Copy application
COPY backend/ ./backend/
COPY shared/ ./shared/
COPY config/ ./config/

# Create data directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 45680

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:45680/health || exit 1

# Run application
CMD ["python", "-m", "backend.training.app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  training-backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: clara-training
    ports:
      - "45680:45680"
    environment:
      - CLARA_SECURITY_MODE=production
      - CLARA_TRAINING_PORT=45680
      - POSTGRES_HOST=postgres
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./configs:/app/configs
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - clara-network

  dataset-backend:
    build:
      context: .
      dockerfile: Dockerfile.dataset
    container_name: clara-dataset
    ports:
      - "45681:45681"
    environment:
      - CLARA_SECURITY_MODE=production
      - CLARA_DATASET_PORT=45681
      - POSTGRES_HOST=postgres
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - clara-network

  postgres:
    image: postgres:14-alpine
    container_name: clara-postgres
    environment:
      - POSTGRES_USER=clara
      - POSTGRES_PASSWORD=clara_password
      - POSTGRES_DB=clara
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - clara-network

  nginx:
    image: nginx:alpine
    container_name: clara-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - training-backend
      - dataset-backend
    restart: unless-stopped
    networks:
      - clara-network

volumes:
  postgres-data:

networks:
  clara-network:
    driver: bridge
```

### Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart single service
docker-compose restart training-backend

# Check status
docker-compose ps
```

---

## Health Checks & Monitoring

### Health Check Endpoints

**Training Backend:**
```bash
GET http://localhost:45680/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "training-backend",
  "version": "2.0.0",
  "port": 45680,
  "active_jobs": 3,
  "worker_pool": {
    "io_workers": 18,
    "cpu_workers": 18
  },
  "timestamp": "2025-11-17T10:30:00Z"
}
```

**Dataset Backend:**
```bash
GET http://localhost:45681/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "dataset-backend",
  "version": "2.0.0",
  "port": 45681,
  "datasets_count": 42,
  "uds3_available": false,
  "timestamp": "2025-11-17T10:30:00Z"
}
```

### Monitoring Script

```python
# check_system_status.py
import requests
import sys

def check_service(name, url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: HEALTHY")
            return True
        else:
            print(f"❌ {name}: UNHEALTHY (HTTP {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ {name}: UNREACHABLE ({str(e)})")
        return False

# Check both backends
training_ok = check_service("Training Backend", "http://localhost:45680/health")
dataset_ok = check_service("Dataset Backend", "http://localhost:45681/health")

sys.exit(0 if training_ok and dataset_ok else 1)
```

**Usage:**
```bash
python check_system_status.py
```

### Prometheus Metrics

**Enable metrics in .env:**
```bash
METRICS_ENABLED=true
METRICS_EXPORT_INTERVAL=60
CLARA_METRICS_PORT=9310
```

**Metrics endpoint:**
```
http://localhost:9310/metrics
```

### Logging

**Log Locations:**
- Development: Console output
- Production (systemd): `journalctl -u clara-training`
- Docker: `docker-compose logs`
- File (if configured): `./logs/clara.log`

**Log Levels:**
- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages (potential issues)
- ERROR: Error messages (requires attention)
- CRITICAL: Critical errors (system failure)

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:**
```
OSError: [Errno 48] Address already in use
```

**Solution:**
```powershell
# Windows: Find process using port
netstat -ano | findstr :45680
taskkill /PID <process_id> /F

# Linux: Find and kill process
sudo lsof -i :45680
sudo kill -9 <process_id>

# Or use stop script
.\stop_backends.ps1  # Windows
sudo systemctl stop clara-training  # Linux
```

#### 2. Connection Refused

**Error:**
```
ConnectionError: Connection refused
```

**Solution:**
```bash
# Check if service is running
curl http://localhost:45680/health

# Check firewall
sudo ufw allow 45680/tcp  # Linux
# Windows: Allow in Windows Firewall

# Check service logs
sudo journalctl -u clara-training -n 50
```

#### 3. Database Connection Failed

**Error:**
```
OperationalError: could not connect to server
```

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h 192.168.178.94 -U postgres -d postgres

# Check .env configuration
cat .env | grep POSTGRES
```

#### 4. UDS3 Not Available

**Warning:**
```
WARNING: UDS3 not available - dataset search will be limited
```

**Status:** ⚠️ NOT CRITICAL

**Explanation:**
- UDS3 is OPTIONAL for advanced search
- All other features work normally
- Datasets can be created manually

**To enable UDS3 (optional):**
```bash
# Install UDS3 package
cd ../uds3
pip install -e .

# Set environment variable
export UDS3_ROOT=/path/to/uds3
```

#### 5. Frontend Connection Failed

**Error in GUI:**
```
Status: 🔴 Connection Failed
```

**Solution:**
```bash
# 1. Check backends are running
curl http://localhost:45680/health
curl http://localhost:45681/health

# 2. Restart backends
.\stop_backends.ps1
.\start_backends.ps1

# 3. Check frontend can reach backends
# In frontend code, verify base_url is correct
```

### Performance Issues

#### High Memory Usage

**Check:**
```bash
# Linux
free -h
htop

# Docker
docker stats
```

**Solutions:**
- Reduce worker pool size in .env
- Reduce MAX_CONCURRENT_JOBS
- Increase system RAM
- Enable swap if needed

#### Slow Training Jobs

**Diagnostics:**
```bash
# Check GPU utilization
nvidia-smi

# Check CPU load
top  # Linux
Get-Process  # Windows
```

**Solutions:**
- Verify CUDA is installed and detected
- Reduce batch size in training config
- Use gradient accumulation
- Enable mixed precision training

---

## Upgrade & Maintenance

### Upgrade Process

**1. Backup Data:**
```bash
# Backup database
pg_dump -h localhost -U postgres clara > backup_$(date +%Y%m%d).sql

# Backup configuration
cp .env .env.backup
cp -r data/ data_backup/
```

**2. Pull Latest Code:**
```bash
cd /opt/VCC-Clara
git fetch
git checkout v2.1.0  # or main
```

**3. Update Dependencies:**
```bash
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

**4. Run Migrations (if any):**
```bash
# Check for migration scripts
ls scripts/migrations/

# Run migrations
python scripts/migrate_*.py
```

**5. Restart Services:**
```bash
# Linux
sudo systemctl restart clara-training
sudo systemctl restart clara-dataset

# Windows
.\stop_backends.ps1
.\start_backends.ps1

# Docker
docker-compose down
docker-compose up -d
```

**6. Verify Health:**
```bash
curl http://localhost:45680/health
curl http://localhost:45681/health
```

### Maintenance Tasks

**Daily:**
- Monitor service health
- Check disk space
- Review error logs

**Weekly:**
- Review audit logs
- Check database size
- Update security patches

**Monthly:**
- Database optimization (VACUUM)
- Log rotation
- Backup verification
- Update dependencies

**Quarterly:**
- Security audit
- Performance review
- Capacity planning

### Log Rotation

**Logrotate Configuration (/etc/logrotate.d/clara):**
```
/opt/VCC-Clara/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 clara clara
    sharedscripts
    postrotate
        systemctl reload clara-training
        systemctl reload clara-dataset
    endscript
}
```

### Database Maintenance

```sql
-- Vacuum and analyze
VACUUM ANALYZE;

-- Check database size
SELECT pg_size_pretty(pg_database_size('clara'));

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Security Checklist

### Production Deployment Checklist

- [ ] CORS limited to specific origins
- [ ] JWT authentication enabled
- [ ] mTLS enabled for service-to-service
- [ ] SSL/TLS certificates configured
- [ ] Secrets in environment variables (not in code)
- [ ] Log levels set to WARNING/ERROR
- [ ] API documentation disabled in production
- [ ] Rate limiting configured
- [ ] Firewall rules configured
- [ ] Database passwords rotated
- [ ] Audit logging enabled
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured

### Security Best Practices

1. **Never commit secrets to git**
2. **Use strong passwords (20+ characters)**
3. **Enable audit logging**
4. **Regularly update dependencies**
5. **Monitor for security advisories**
6. **Implement principle of least privilege**
7. **Use TLS for all external communication**
8. **Regular security audits**

---

## Support & Resources

### Documentation

- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Configuration Reference](./CONFIGURATION_REFERENCE.md) - All config options
- [Architecture](./ARCHITECTURE.md) - System architecture
- [Frontend Guide](./FRONTEND_GUIDE.md) - Frontend applications

### Health Check Script

```powershell
# PowerShell health check
$services = @(
    @{Name="Training"; Url="http://localhost:45680/health"},
    @{Name="Dataset"; Url="http://localhost:45681/health"}
)

foreach ($service in $services) {
    try {
        $response = Invoke-RestMethod -Uri $service.Url -TimeoutSec 5
        Write-Host "✅ $($service.Name): $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($service.Name): FAILED" -ForegroundColor Red
    }
}
```

### Quick Reference

**Start System:**
- Windows: `.\start_clara.ps1`
- Linux: `sudo systemctl start clara-training clara-dataset`
- Docker: `docker-compose up -d`

**Stop System:**
- Windows: `.\stop_backends.ps1`
- Linux: `sudo systemctl stop clara-training clara-dataset`
- Docker: `docker-compose down`

**Health Check:**
- `curl http://localhost:45680/health`
- `curl http://localhost:45681/health`

**Logs:**
- Linux: `sudo journalctl -u clara-training -f`
- Docker: `docker-compose logs -f`

---

**Version:** 2.0.0  
**Last Updated:** 2025-11-17  
**Status:** ✅ Production Ready
