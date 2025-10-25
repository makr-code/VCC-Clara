# CLARA Security Framework - Environment-Variable Controlled

**Version:** 1.0  
**Author:** VCC Team  
**Date:** 2024-10-24

## Overview

Das CLARA Training System Security Framework bietet **flexible, umgebungsbasierte Sicherheitskonfiguration** für verschiedene Deployment-Szenarien. Das Framework unterstützt **4 Security-Modi** von vollständiger Produktions-Sicherheit bis zu Debug-Modi ohne Authentifizierung.

### Key Features

✅ **Environment-Variable Control** - Komplette Steuerung via `.env` Datei  
✅ **4 Security Modes** - Production, Development, Debug, Testing  
✅ **JWT + mTLS Support** - Enterprise-Grade Authentication & Encryption  
✅ **RBAC Integration** - 5 Rollen (admin, trainer, analyst, user, auditor)  
✅ **Graceful Degradation** - System funktioniert auch ohne Keycloak (Debug-Mode)  
✅ **Zero-Code Changes** - Alle Einstellungen via Environment-Variables

---

## Security Modes

### 1. Production Mode (Default)

**Verwendung:** Production Deployments mit vollständiger Sicherheit

```bash
CLARA_SECURITY_MODE=production
CLARA_JWT_ENABLED=true
CLARA_MTLS_ENABLED=true
```

**Features:**
- ✅ Full JWT Validation (Keycloak RS256)
- ✅ mTLS für Service-to-Service Communication
- ✅ RBAC Enforcement (Role-Based Access Control)
- ✅ Audit Logging für alle Security Events
- ✅ Token Expiration Checks
- ✅ Issuer & Audience Validation

**Requirements:**
- Keycloak Server (Port 8080)
- VCC User Service (Port 5001)
- PKI Service (Port 8443) für mTLS
- PostgreSQL für Audit Logs

---

### 2. Development Mode

**Verwendung:** Lokale Entwicklung mit Keycloak-Integration

```bash
CLARA_SECURITY_MODE=development
CLARA_JWT_ENABLED=true
CLARA_MTLS_ENABLED=false
```

**Features:**
- ✅ JWT Validation (Keycloak RS256)
- ✅ RBAC Enforcement
- ⚠️ **KEIN mTLS** (Service-to-Service via HTTP)
- ✅ Relaxed Logging (DEBUG Level)
- ✅ Swagger/ReDoc UI enabled

**Requirements:**
- Keycloak Server (Port 8080)
- VCC User Service (Port 5001) optional

**Use Cases:**
- Frontend-Entwicklung mit echtem Login-Flow
- API-Testing mit Postman/curl (JWT Token erforderlich)
- Integration-Tests mit Keycloak-Mock

---

### 3. Debug Mode ⚠️

**Verwendung:** Lokale Entwicklung **OHNE** Security (⚠️ NEVER in Production!)

```bash
CLARA_SECURITY_MODE=debug
CLARA_JWT_ENABLED=false
CLARA_MTLS_ENABLED=false
DEBUG_USER_EMAIL=dev@clara.local
DEBUG_USER_ROLES=admin,trainer,analyst
```

**Features:**
- ⚠️ **NO JWT VALIDATION** - Alle Requests werden akzeptiert
- ⚠️ **NO mTLS** - HTTP only
- ✅ Mock User mit konfigurierbaren Rollen
- ✅ Alle API Endpoints offen
- ✅ Maximale Entwicklungsgeschwindigkeit

**Mock User Claims:**
```json
{
  "sub": "debug-user",
  "email": "dev@clara.local",
  "preferred_username": "debug",
  "realm_access": {
    "roles": ["admin", "trainer", "analyst"]
  },
  "debug_mode": true
}
```

**Requirements:**
- **KEINE** - System läuft standalone

**Use Cases:**
- Schnelle Entwicklung/Prototyping
- Offline-Entwicklung (kein Keycloak verfügbar)
- Unit-Tests ohne externe Dependencies

**⚠️ SECURITY WARNING:**
```
DEBUG MODE BYPASSES ALL SECURITY!
- NO Authentication
- NO Authorization
- NO Audit Logging
- NEVER use in production!
```

---

### 4. Testing Mode

**Verwendung:** Unit & Integration Tests

```bash
CLARA_SECURITY_MODE=testing
LOG_LEVEL=DEBUG
```

**Features:**
- ✅ Mock JWT Validation (keine Keycloak-Verbindung)
- ✅ Test-User mit konfigurierbaren Rollen
- ✅ Fast Execution (keine externen API-Calls)
- ✅ Predictable Behavior

**Use Cases:**
- Pytest Unit Tests
- CI/CD Pipelines
- Load Testing ohne Keycloak-Overhead

---

## Configuration Reference

### Environment Variables

#### Security Mode Selection

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `CLARA_SECURITY_MODE` | `production`, `development`, `debug`, `testing` | `production` | Master security mode selector |
| `CLARA_JWT_ENABLED` | `true`, `false` | `true` | Enable/disable JWT validation (overrides mode) |
| `CLARA_MTLS_ENABLED` | `true`, `false` | `false` | Enable/disable mTLS for service-to-service |

#### Keycloak Configuration

| Variable | Example | Default | Description |
|----------|---------|---------|-------------|
| `KEYCLOAK_URL` | `http://localhost:8080` | `http://localhost:8080` | Keycloak server URL |
| `KEYCLOAK_REALM` | `vcc` | `vcc` | Keycloak realm name |
| `KEYCLOAK_CLIENT_ID` | `clara-training-system` | `clara-training-system` | OAuth2 client ID |
| `JWT_ALGORITHM` | `RS256` | `RS256` | JWT signing algorithm |

#### Debug Mode Configuration

| Variable | Example | Default | Description |
|----------|---------|---------|-------------|
| `DEBUG_USER_ID` | `debug-user` | `debug-user` | Mock user ID |
| `DEBUG_USER_EMAIL` | `dev@clara.local` | `debug@clara.local` | Mock user email |
| `DEBUG_USER_ROLES` | `admin,trainer` | `admin,trainer` | Comma-separated roles |

---

## Usage Examples

### FastAPI Integration

#### 1. Protect Endpoint with JWT

```python
from fastapi import FastAPI, Depends
from shared.jwt_middleware import jwt_middleware

app = FastAPI()

@app.post("/api/training/jobs")
async def create_training_job(
    request: TrainingJobRequest,
    user: dict = Depends(jwt_middleware.get_current_user)
):
    """
    Protected endpoint - requires valid JWT token
    
    Security Behavior:
    - production/development: Validates JWT token
    - debug: Returns mock user (no validation)
    - testing: Returns test user (no validation)
    """
    user_email = user["email"]
    user_id = user["sub"]
    
    return {"status": "created", "user": user_email}
```

#### 2. Role-Based Access Control (RBAC)

```python
from shared.jwt_middleware import jwt_middleware

@app.delete("/api/training/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer"]))
):
    """
    Protected endpoint - requires admin OR trainer role
    
    Security Behavior:
    - production/development: Validates JWT + checks roles
    - debug: Returns mock user with admin+trainer roles
    - testing: Returns test user
    """
    return {"status": "cancelled", "job_id": job_id}
```

#### 3. Admin-Only Endpoint

```python
@app.post("/api/config/update")
async def update_config(
    config: ConfigUpdate,
    user: dict = Depends(jwt_middleware.require_roles(["admin"]))
):
    """
    Protected endpoint - requires admin role
    
    Security Behavior:
    - production/development: Validates JWT, checks admin role
    - debug: Returns mock user (bypasses role check)
    - testing: Returns test user
    """
    return {"status": "updated"}
```

#### 4. Optional Authentication

```python
@app.get("/api/datasets/public")
async def list_datasets(
    user: Optional[dict] = Depends(jwt_middleware.optional_auth())
):
    """
    Public endpoint with optional authentication
    
    Security Behavior:
    - production/development: Validates JWT if present, None otherwise
    - debug: Always returns mock user
    - testing: Returns test user if token present
    """
    if user:
        return {"datasets": [...], "user": user["email"]}
    else:
        return {"datasets": [...], "user": "anonymous"}
```

---

## Startup Examples

### Production Deployment

```bash
# .env file
CLARA_SECURITY_MODE=production
CLARA_JWT_ENABLED=true
CLARA_MTLS_ENABLED=true
KEYCLOAK_URL=https://auth.vcc.local
KEYCLOAK_REALM=vcc
KEYCLOAK_CLIENT_ID=clara-training-system
LOG_LEVEL=INFO
ENABLE_API_DOCS=false

# Start service
python scripts/clara_training_backend.py
```

**Expected Output:**
```
============================================================
CLARA Security Configuration
============================================================
Security Mode: PRODUCTION
JWT Enabled: True
mTLS Enabled: True
Keycloak URL: https://auth.vcc.local
Realm: vcc
Client ID: clara-training-system
============================================================
INFO: Fetching JWKS from: https://auth.vcc.local/realms/vcc/protocol/openid-connect/certs
INFO: JWT public key cached successfully
INFO: PKI Client initialized: localhost:8443
INFO: Service certificate: ./service_certificates/clara-training.crt
INFO: Training Backend started on http://0.0.0.0:45680
```

---

### Local Development (with Keycloak)

```bash
# .env file
CLARA_SECURITY_MODE=development
LOG_LEVEL=DEBUG
HOT_RELOAD=true

# Start service
python scripts/clara_training_backend.py
```

**Expected Output:**
```
============================================================
CLARA Security Configuration
============================================================
Security Mode: DEVELOPMENT
JWT Enabled: True
mTLS Enabled: False
Keycloak URL: http://localhost:8080
Realm: vcc
Client ID: clara-training-system
============================================================
DEBUG: JWT validation enabled, mTLS disabled
INFO: Training Backend started on http://0.0.0.0:45680
INFO: Swagger UI available at http://localhost:45680/docs
```

---

### Local Development (Debug Mode - No Security)

```bash
# .env file
CLARA_SECURITY_MODE=debug
LOG_LEVEL=DEBUG
DEBUG_USER_EMAIL=dev@clara.local
DEBUG_USER_ROLES=admin,trainer,analyst

# Start service
python scripts/clara_training_backend.py
```

**Expected Output:**
```
============================================================
CLARA Security Configuration
============================================================
Security Mode: DEBUG
JWT Enabled: False
mTLS Enabled: False
⚠️  DEBUG MODE ACTIVE - NO SECURITY ENFORCEMENT!
   Debug User: dev@clara.local
   Debug Roles: ['admin', 'trainer', 'analyst']
============================================================
WARNING: Running in DEBUG mode - all security checks disabled!
INFO: Training Backend started on http://0.0.0.0:45680
```

---

### Unit Testing

```bash
# .env.test file
CLARA_SECURITY_MODE=testing
LOG_LEVEL=DEBUG

# Run tests
CLARA_SECURITY_MODE=testing pytest tests/test_training_backend.py -v
```

**Test Example:**
```python
import pytest
from fastapi.testclient import TestClient
from scripts.clara_training_backend import app

# No Keycloak needed - testing mode uses mock JWT
def test_create_job():
    client = TestClient(app)
    
    # Mock JWT token (not validated in testing mode)
    headers = {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9..."}
    
    response = client.post(
        "/api/training/jobs",
        json={"dataset_id": "test", "trainer_type": "lora"},
        headers=headers
    )
    
    assert response.status_code == 200
```

---

## Security Best Practices

### DO ✅

1. **Use Production Mode in Production**
   ```bash
   CLARA_SECURITY_MODE=production
   CLARA_JWT_ENABLED=true
   CLARA_MTLS_ENABLED=true
   ```

2. **Use Development Mode for Local Dev with Keycloak**
   ```bash
   CLARA_SECURITY_MODE=development
   ```

3. **Use Debug Mode ONLY for Offline Development**
   ```bash
   CLARA_SECURITY_MODE=debug  # Only on localhost!
   ```

4. **Validate .env File on Startup**
   ```python
   if os.getenv("CLARA_SECURITY_MODE") == "debug" and os.getenv("PRODUCTION", "false") == "true":
       raise ValueError("DEBUG mode not allowed in production!")
   ```

5. **Log Security Mode on Startup**
   - Bereits implementiert in `SecurityConfig._log_config()`

### DON'T ❌

1. **NEVER Use Debug Mode in Production**
   ```bash
   # ❌ NEVER DO THIS IN PRODUCTION
   CLARA_SECURITY_MODE=debug
   ```

2. **Don't Disable JWT in Production**
   ```bash
   # ❌ NEVER DO THIS IN PRODUCTION
   CLARA_JWT_ENABLED=false
   ```

3. **Don't Commit .env Files to Git**
   ```bash
   # Add to .gitignore
   .env
   .env.local
   .env.production
   ```

4. **Don't Use Weak Debug Passwords**
   ```bash
   # ❌ DON'T
   DEBUG_USER_ID=admin
   DEBUG_USER_EMAIL=admin@admin.com
   ```

---

## Monitoring & Auditing

### Security Event Logging

```python
# Automatically logged by jwt_middleware.py
logger.warning("JWT token expired")  # Status 401
logger.warning("Invalid JWT token")  # Status 401
logger.warning("User missing required roles")  # Status 403
logger.info("Token verified for user: {email}")  # Success
```

### Audit Log Example

```json
{
  "timestamp": "2024-10-24T10:30:00Z",
  "event": "authentication_success",
  "user_id": "user-123",
  "user_email": "trainer@vcc.local",
  "ip_address": "192.168.1.100",
  "endpoint": "/api/training/jobs",
  "method": "POST",
  "security_mode": "production"
}
```

### Prometheus Metrics

```python
# Already defined in clara_training_backend.py
authentication_failures = Counter('authentication_failures_total', 'Total authentication failures')
authorization_failures = Counter('authorization_failures_total', 'Total authorization failures')
active_users = Gauge('active_authenticated_users', 'Number of active authenticated users')
```

---

## Troubleshooting

### Issue: "Authentication service unavailable" (503)

**Cause:** Keycloak nicht erreichbar

**Solution:**
```bash
# Check Keycloak status
curl http://localhost:8080/realms/vcc/.well-known/openid-configuration

# Or switch to debug mode for offline development
CLARA_SECURITY_MODE=debug python scripts/clara_training_backend.py
```

---

### Issue: "Missing authentication credentials" (401)

**Cause:** Kein Authorization Header

**Solution:**
```bash
# Add JWT token to request
curl -H "Authorization: Bearer <JWT_TOKEN>" http://localhost:45680/api/training/jobs
```

---

### Issue: "Insufficient permissions" (403)

**Cause:** User hat nicht die erforderlichen Rollen

**Solution:**
```bash
# Check user roles in Keycloak
# Or use debug mode with elevated roles
DEBUG_USER_ROLES=admin,trainer python scripts/clara_training_backend.py
```

---

## Migration Guide

### From No Security → Environment-Based Security

**Before (Hardcoded):**
```python
# ❌ Old approach
JWT_ENABLED = True  # Hardcoded
KEYCLOAK_URL = "http://localhost:8080"  # Hardcoded

def get_current_user(token: str):
    # Always validates token
    payload = jwt.decode(token, PUBLIC_KEY, ...)
    return payload
```

**After (Environment-Based):**
```python
# ✅ New approach
from shared.jwt_middleware import jwt_middleware

@app.get("/protected")
async def route(user: dict = Depends(jwt_middleware.get_current_user)):
    # Validates token in production/development
    # Returns mock user in debug mode
    # Behavior controlled via CLARA_SECURITY_MODE env var
    return {"user": user["email"]}
```

**Benefits:**
- ✅ Zero code changes to switch modes
- ✅ Same code for dev/staging/production
- ✅ Easy offline development (debug mode)
- ✅ Fast testing (testing mode)

---

## Conclusion

Das **Environment-Variable Controlled Security Framework** bietet:

✅ **Flexibilität** - 4 Modi für verschiedene Szenarien  
✅ **Sicherheit** - Production-ready JWT + mTLS  
✅ **Developer Experience** - Debug mode für schnelle Entwicklung  
✅ **Zero-Code Changes** - Komplette Steuerung via `.env`  
✅ **Graceful Degradation** - System funktioniert auch ohne Keycloak

**Empfohlene Modi:**
- **Production:** `CLARA_SECURITY_MODE=production` (Full Security)
- **Development:** `CLARA_SECURITY_MODE=development` (JWT only)
- **Offline Dev:** `CLARA_SECURITY_MODE=debug` (No Security)
- **Testing:** `CLARA_SECURITY_MODE=testing` (Mock Security)

---

## References

- `shared/jwt_middleware.py` - JWT Middleware Implementation
- `.env.example` - Environment Variable Reference
- `docs/SELF_LEARNING_LORA_SYSTEM_ARCHITECTURE.md` - System Architecture
- `c:/VCC/user/README.md` - VCC User Service Documentation
- `c:/VCC/PKI/README.md` - PKI Service Documentation
