# VCC-Clara CD Pipeline & Deployment Guide

**Phase 1: Week 2 Implementation**  
**Created:** 2025-11-23  
**Status:** ✅ Active

---

## 🎯 Overview

Continuous Deployment (CD) pipelines for VCC-Clara across all environments using on-premise infrastructure.

### Environments

- **Development** - Auto-deploy from `develop` branch
- **Staging** - Manual deployment for pre-production testing  
- **Production** - Manual deployment with approval and rollback

---

## 🚀 Quick Start

### Development Deployment

```bash
# Triggered automatically on push to develop branch
# Or manually:
cd deployment/dev
export POSTGRES_PASSWORD=dev_password
./deploy.sh
```

### Staging Deployment

```bash
# Manually trigger via GitHub Actions
# Then download artifacts:
cd deployment/staging
export POSTGRES_PASSWORD=staging_password
docker-compose up -d
```

### Production Deployment

```bash
# 1. Trigger via GitHub Actions with version tag (e.g., v1.0.0)
# 2. Download production deployment artifact
# 3. Deploy:
cd deployment/production
export POSTGRES_PASSWORD=prod_password
./deploy.sh

# Rollback if needed:
./rollback.sh
```

---

## 📦 Workflows

### CD - Development (`.github/workflows/cd-dev.yml`)

**Triggers:**
- Push to `develop` branch
- Manual dispatch

**Features:**
- Automatic deployment
- Docker Compose configuration
- Health checks
- Deployment artifacts

### CD - Staging (`.github/workflows/cd-staging.yml`)

**Triggers:**
- Push to `staging` branch
- Manual dispatch

**Features:**
- Production-like security
- Resource limits
- Pre-deployment smoke tests
- Deployment artifacts

### CD - Production (`.github/workflows/cd-prod.yml`)

**Triggers:**
- Manual dispatch only
- Requires version tag (e.g., v1.0.0)
- Confirmation required: "deploy-production"

**Features:**
- Full security (JWT + mTLS)
- Health checks with retries
- Automated backup integration
- Rollback script
- Deployment audit trail
- Resource limits (4 CPU / 8GB RAM per service)

---

## 🔒 Security

| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| JWT | ❌ | ✅ | ✅ |
| mTLS | ❌ | ❌ | ✅ |
| Resource Limits | ❌ | ✅ | ✅ |
| Backups | ❌ | ✅ | ✅ |

---

## 📊 Monitoring

Health checks available at:
- Training Backend: `http://localhost:45680/health`
- Datasets Backend: `http://localhost:45681/health`

Logs:
```bash
docker-compose logs -f
```

---

## 🔄 Rollback

Production rollback:
```bash
cd deployment/production
./rollback.sh
# Enter version to rollback to when prompted
```

---

## 📝 Deployment Checklist

- [ ] CI checks passing
- [ ] Code reviewed
- [ ] Backup verified (production)
- [ ] Deploy script downloaded
- [ ] Environment variables set
- [ ] Deploy executed
- [ ] Health checks passed
- [ ] Logs verified
- [ ] Stakeholders notified

---

**See:** [Full Deployment Guide](DEPLOYMENT_GUIDE.md) for detailed instructions.
