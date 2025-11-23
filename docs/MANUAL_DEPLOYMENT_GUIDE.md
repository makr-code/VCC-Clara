# VCC-Clara Manual Deployment Guide

**Deployment Strategy:** Manual, Offline  
**Build Strategy:** Offline Package  
**Infrastructure:** On-Premise Only  
**Created:** 2025-11-23

---

## 🎯 Overview

VCC-Clara uses a **manual deployment** strategy with **offline build packages**. This approach:
- Eliminates automated deployments for maximum control
- Creates portable offline packages
- Supports air-gapped environments
- No vendor lock-in or cloud dependencies

---

## 📦 Build Process

### Triggering a Build

Builds are triggered via GitHub Actions but create **offline deployment packages** (not automated deployments):

```bash
# Via Git tag
git tag v1.0.0
git push origin v1.0.0

# Via GitHub Actions UI
# Go to Actions → "Build Offline Deployment Package" → Run workflow
# Enter version: v1.0.0
```

### Build Output

The build process creates:
- **Docker images** (compressed tar.gz files)
- **Docker Compose** configurations
- **Deployment scripts**
- **Documentation**
- **Complete offline package** (single tar.gz)

All packaged in: `vcc-clara-offline-VERSION.tar.gz`

---

## 🚀 Manual Deployment

### Step 1: Download Package

Download the offline package from GitHub Actions artifacts:

1. Go to GitHub Actions
2. Find the workflow run
3. Download `vcc-clara-offline-VERSION`
4. Transfer to target server (USB, network, etc.)

### Step 2: Extract Package

```bash
tar xzf vcc-clara-offline-v1.0.0.tar.gz
cd offline-deployment
```

### Step 3: Load Docker Images

```bash
cd scripts

# Load images into Docker
gunzip -c ../images/training-backend.tar.gz | docker load
gunzip -c ../images/datasets-backend.tar.gz | docker load

# Verify
docker images | grep vcc-clara
```

### Step 4: Configure Environment

**Development:**
```bash
# Optional: Set custom password
export POSTGRES_PASSWORD=dev_password
```

**Production:**
```bash
# Required: Set secure password
export POSTGRES_PASSWORD=$(openssl rand -base64 32)

# Optional: Custom settings
export CLARA_JWT_SECRET=$(openssl rand -base64 64)
```

### Step 5: Deploy

```bash
# Development
cd configs
docker-compose -f docker-compose-dev.yml up -d

# Production
docker-compose -f docker-compose-prod.yml up -d
```

### Step 6: Verify Deployment

```bash
# Wait for startup
sleep 15

# Health checks
curl http://localhost:45680/health  # Training Backend
curl http://localhost:45681/health  # Datasets Backend

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 🔧 Management Operations

### Stop Services

```bash
cd configs
docker-compose -f docker-compose-dev.yml down  # or docker-compose-prod.yml
```

### Restart Services

```bash
docker-compose restart
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f training-backend

# Last 100 lines
docker-compose logs --tail=100
```

### Update to New Version

```bash
# 1. Download new offline package
tar xzf vcc-clara-offline-v1.1.0.tar.gz

# 2. Stop current services
cd offline-deployment-old/configs
docker-compose down

# 3. Load new images
cd ../../offline-deployment/scripts
gunzip -c ../images/training-backend.tar.gz | docker load
gunzip -c ../images/datasets-backend.tar.gz | docker load

# 4. Deploy new version
cd ../configs
docker-compose up -d
```

---

## 📋 Requirements

### Minimum (Development)
- Docker 24.0+
- Docker Compose 2.0+
- 4 CPU cores
- 8GB RAM
- 50GB storage

### Recommended (Production)
- Docker 24.0+
- Docker Compose 2.0+
- 8 CPU cores
- 16GB RAM
- 100GB SSD storage
- Dedicated database server (optional)

---

## 🔒 Security

### Development Environment
- Basic security mode
- Default PostgreSQL password (can be changed)
- JWT authentication disabled
- For testing only

### Production Environment
- Production security mode
- **Mandatory:** Custom PostgreSQL password
- JWT authentication enabled
- Resource limits enforced
- Regular backups required

### Best Practices

1. **Never use default passwords in production**
2. **Store secrets securely** (e.g., HashiCorp Vault)
3. **Regular backups** before updates
4. **Test in dev** before production deployment
5. **Monitor logs** after deployment
6. **Document changes** in deployment log

---

## 💾 Backup & Restore

### Backup Database

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U postgres clara_production > backup_$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v vcc-clara_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/volumes_$(date +%Y%m%d).tar.gz /data
```

### Restore Database

```bash
# Restore from backup
cat backup_20251123.sql | docker-compose exec -T postgres psql -U postgres clara_production

# Verify
docker-compose exec postgres psql -U postgres -d clara_production -c "SELECT COUNT(*) FROM documents;"
```

---

## 🔍 Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check ports
sudo netstat -tlnp | grep ':45680\|:45681\|:5432'

# Restart services
docker-compose restart
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
docker-compose exec postgres psql -U postgres -l

# Check environment variables
docker-compose exec training-backend env | grep DATABASE_URL
```

### Image Loading Fails

```bash
# Verify image file integrity
gunzip -t images/training-backend.tar.gz

# Check Docker disk space
docker system df

# Clean up if needed
docker system prune -a
```

---

## 📊 Monitoring

### Health Checks

```bash
# Automated health check script
cat > health-check.sh <<'EOF'
#!/bin/bash
STATUS=0
if ! curl -f http://localhost:45680/health >/dev/null 2>&1; then
  echo "❌ Training Backend unhealthy"
  STATUS=1
fi
if ! curl -f http://localhost:45681/health >/dev/null 2>&1; then
  echo "❌ Datasets Backend unhealthy"
  STATUS=1
fi
if [ $STATUS -eq 0 ]; then
  echo "✅ All services healthy"
fi
exit $STATUS
EOF
chmod +x health-check.sh

# Run health check
./health-check.sh
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Logs size
du -sh /var/lib/docker/containers/*
```

---

## 📝 Deployment Checklist

### Pre-Deployment
- [ ] Offline package downloaded
- [ ] Package integrity verified
- [ ] Target server meets requirements
- [ ] Backup of current system (if updating)
- [ ] Postgres password prepared (production)
- [ ] Firewall rules configured
- [ ] Team notified of deployment window

### During Deployment
- [ ] Services stopped (if updating)
- [ ] Images loaded successfully
- [ ] Environment variables set
- [ ] docker-compose up executed
- [ ] Health checks passing

### Post-Deployment
- [ ] All services running
- [ ] Health endpoints responding
- [ ] Logs checked for errors
- [ ] Basic functionality tested
- [ ] Deployment documented
- [ ] Team notified of completion

---

## 🎓 Best Practices

1. **Always test in development first**
2. **Keep offline packages versioned**
3. **Backup before any changes**
4. **Monitor logs during deployment**
5. **Document every deployment**
6. **Maintain deployment history**
7. **Plan rollback strategy**
8. **Test health checks regularly**

---

## 📞 Support

**Issues:**
- Create GitHub issue with `deployment` label
- Include version, environment, logs
- Describe steps to reproduce

**Emergency:**
- Stop services: `docker-compose down`
- Restore from backup
- Contact team lead

---

## 📚 Related Documentation

- [Phase 1 Kickoff](PHASE_1_KICKOFF.md)
- [Architecture](VCC_CLARA_WEITERENTWICKLUNGSSTRATEGIE.md)
- [Build Process](.github/workflows/build.yml)

---

**Manual Deployment | On-Premise | Vendor-Agnostic | Offline-Capable**

**Last Updated:** 2025-11-23
