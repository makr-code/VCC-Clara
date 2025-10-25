# Clara Configuration Management

Centralized configuration using Pydantic Settings with environment-based overrides.

## 📋 Overview

The `config/` package provides **type-safe, environment-based configuration** for all Clara services:

- ✅ **Pydantic Settings** - Type validation and IDE autocomplete
- ✅ **Environment Variables** - Override via `.env` files or system env
- ✅ **Multiple Environments** - Development, Production, Testing
- ✅ **Computed Properties** - Auto-generated URLs and DSNs
- ✅ **Backward Compatible** - Works with legacy code

## 📁 Structure

```
config/
├── __init__.py          # Package exports, config factory
├── base.py              # BaseConfig (Pydantic Settings)
├── development.py       # Development overrides
├── production.py        # Production overrides
├── testing.py           # Testing overrides
└── README.md            # This file
```

## 🚀 Quick Start

### Basic Usage

```python
# Import default config (auto-detects environment)
from config import config

print(f"Training Port: {config.training_port}")
print(f"Dataset Port: {config.dataset_port}")
print(f"Security Mode: {config.security_mode.value}")
```

### Environment-Specific Config

```python
from config import get_config

# Explicitly load environment
dev_config = get_config("development")
prod_config = get_config("production")
test_config = get_config("testing")
```

### Direct Import

```python
from config.production import prod_config
from config.development import dev_config
from config.testing import test_config
```

## 🌍 Environment Variables

Config reads from environment variables with `CLARA_` prefix:

### Application Settings
- `CLARA_ENVIRONMENT` - Environment type (development/production/testing)
- `CLARA_DEBUG` - Enable debug mode (true/false)
- `CLARA_LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)

### API Settings
- `CLARA_API_HOST` - API bind host (default: 0.0.0.0)
- `CLARA_API_PORT` - API port (default: 8000)
- `CLARA_API_WORKERS` - Worker count (default: 4)
- `CLARA_API_RELOAD` - Hot reload (default: false)

### Backend Service Ports
- `CLARA_TRAINING_PORT` - Training backend port (default: 45680)
- `CLARA_DATASET_PORT` - Dataset backend port (default: 45681)

### Worker Configuration
- `CLARA_MAX_CONCURRENT_JOBS` - Max parallel jobs (default: 2)
- `CLARA_WORKER_TIMEOUT` - Worker timeout in seconds (default: 3600)

### Security Settings
- `CLARA_SECURITY_MODE` - Security mode (production/development/debug/testing)
- `CLARA_JWT_ENABLED` - Enable JWT (true/false)
- `CLARA_MTLS_ENABLED` - Enable mTLS (true/false)

### Keycloak Settings
- `KEYCLOAK_URL` - Keycloak URL (default: http://localhost:8080)
- `KEYCLOAK_REALM` - Realm name (default: vcc)
- `KEYCLOAK_CLIENT_ID` - Client ID (default: clara-training-system)
- `JWT_ALGORITHM` - JWT algorithm (default: RS256)

### Database Settings (UDS3)
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DATABASE`
- `CHROMA_HOST`, `CHROMA_PORT`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
- `COUCH_URL`, `COUCH_USER`, `COUCH_PASSWORD`

## 📄 .env Files

### Development Setup

1. Copy template:
   ```bash
   cp .env.dev .env
   ```

2. Edit `.env` with your local settings

3. Config auto-loads from `.env`

### Environment-Specific Templates

- `.env.dev` - Development environment (local services)
- `.env.prod` - Production environment (remote services)
- `.env.test` - Testing environment (test databases)

### Priority Order

1. System environment variables (highest priority)
2. `.env` file in project root
3. Default values in `config/base.py` (lowest priority)

## 🔧 Computed Properties

Config provides auto-generated properties:

```python
from config import config

# Keycloak URLs
print(config.keycloak_issuer)      # http://localhost:8080/realms/vcc
print(config.keycloak_jwks_url)    # .../protocol/openid-connect/certs

# Database DSN
print(config.postgres_dsn)         # postgresql://user:pass@host:port/db

# Environment checks
if config.is_development:
    print("Running in development mode")

# Security resolution
print(config.jwt_enabled_resolved)  # True/False based on security_mode
print(config.mtls_enabled_resolved) # True/False based on security_mode
```

## 🏗️ Architecture

### BaseConfig (base.py)

- **Type**: Pydantic Settings
- **Features**: Type validation, .env loading, defaults
- **Fields**: 50+ configuration options
- **Properties**: 8 computed properties

### Environment Configs

- **DevelopmentConfig**: Local development, JWT only, no mTLS
- **ProductionConfig**: Full security (JWT + mTLS), remote services
- **TestingConfig**: Mock security, test databases

### Config Factory

```python
def get_config(env: str = None) -> BaseConfig:
    """
    Factory function - returns environment-specific config.
    
    - Reads CLARA_ENVIRONMENT if env is None
    - Returns DevelopmentConfig for "development"
    - Returns ProductionConfig for "production"
    - Returns TestingConfig for "testing"
    """
```

## 🔄 Migration from Legacy Code

### Old Code (deprecated)

```python
# shared/auth/models.py (deprecated)
from shared.auth.models import SecurityConfig, get_security_config

cfg = get_security_config()
print(cfg.keycloak_url)
```

### New Code (recommended)

```python
# config package (new)
from config import config

print(config.keycloak_url)
```

### Backward Compatibility

- `shared.auth.models.SecurityConfig` is **deprecated** but still works
- Redirects to `config.config` internally
- Logs deprecation warning on import
- **Action Required**: Update code to use `config` package

## 🧪 Testing

### Test Config Import

```python
python -c "from config import config; print(f'Environment: {config.environment.value}')"
```

### Test Environment Override

```bash
# Set environment
export CLARA_ENVIRONMENT=production

# Verify
python -c "from config import config; print(f'Env: {config.environment.value}')"
```

### Test Computed Properties

```python
python -c "from config import config; print(config.keycloak_issuer)"
```

## 📊 Config Summary

| Category | Fields | Examples |
|----------|--------|----------|
| Application | 4 | app_name, environment, debug, log_level |
| API | 4 | api_host, api_port, api_workers, api_reload |
| Backends | 2 | training_port, dataset_port |
| Workers | 2 | max_concurrent_jobs, worker_timeout |
| Security | 10 | security_mode, jwt_enabled, keycloak_url |
| Database | 16 | postgres_host, chroma_host, neo4j_uri |
| Paths | 4 | project_root, data_dir, models_dir, logs_dir |
| **Total** | **42** | + 8 computed properties |

## 🔐 Security Modes

| Mode | JWT | mTLS | Use Case |
|------|-----|------|----------|
| `production` | ✅ | ✅ | Production deployment |
| `development` | ✅ | ❌ | Local development with Keycloak |
| `debug` | ❌ | ❌ | Local testing (mock user) |
| `testing` | ❌ | ❌ | Pytest tests (mock security) |

## 📚 Examples

### Backend Service

```python
# backend/training/app.py
from config import config

SERVICE_PORT = config.training_port
MAX_CONCURRENT_JOBS = config.max_concurrent_jobs

logging.basicConfig(level=getattr(logging, config.log_level))
```

### Database Connection

```python
from config import config

# PostgreSQL
conn = psycopg2.connect(config.postgres_dsn)

# Or individual values
conn = psycopg2.connect(
    host=config.postgres_host,
    port=config.postgres_port,
    user=config.postgres_user,
    password=config.postgres_password,
    database=config.postgres_database
)
```

### Security Middleware

```python
from config import config

if config.jwt_enabled_resolved:
    # Use real JWT
    from shared.auth import jwt_middleware
else:
    # Use mock security
    jwt_middleware = None
```

## 🛠️ Development Workflow

1. **Copy .env template**: `cp .env.dev .env`
2. **Edit local values**: Update ports, passwords, etc.
3. **Import config**: `from config import config`
4. **Use typed properties**: `config.training_port`
5. **IDE autocomplete**: Full IntelliSense support

## 📈 Next Steps

- [ ] **Phase 5**: Update all scripts to use `config` package
- [ ] **Phase 6**: Validate all services with new config
- [ ] **Phase 7**: Remove deprecated `shared/auth/models.py`
- [ ] **Phase 8**: Git commit with breaking changes note

## 📞 Support

For questions or issues with configuration:
1. Check this README
2. See `.env.dev`, `.env.prod`, `.env.test` templates
3. Review `config/base.py` for all available options
4. Check migration guide: `docs/MIGRATION_GUIDE.md`

---

**Status**: ✅ Production Ready (Phase 4 Complete)  
**Version**: 1.0.0  
**Last Updated**: 2025-10-24
