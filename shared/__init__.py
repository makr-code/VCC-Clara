"""
Shared Package

Shared modules for CLARA services
"""

# Auth
try:
    from .auth import (
        jwt_middleware,
        JWTMiddleware,
        security_config,
        SecurityConfig,
        SecurityMode,
        get_current_user_email,
        get_current_user_id,
        get_current_user_roles
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False
    jwt_middleware = None
    JWTMiddleware = None
    security_config = None
    get_current_user_email = lambda user: user.get("email", "unknown")

# Database
try:
    from .database import (
        DatasetSearchAPI,
        DatasetSearchQuery,
        DatasetDocument,
        UDS3_AVAILABLE
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    DatasetSearchAPI = None
    DatasetSearchQuery = None
    DatasetDocument = None
    UDS3_AVAILABLE = False

__version__ = "1.0.0"

__all__ = [
    # Auth
    "jwt_middleware",
    "JWTMiddleware",
    "security_config",
    "SecurityConfig",
    "SecurityMode",
    "get_current_user_email",
    "get_current_user_id",
    "get_current_user_roles",
    "AUTH_AVAILABLE",
    
    # Database
    "DatasetSearchAPI",
    "DatasetSearchQuery",
    "DatasetDocument",
    "UDS3_AVAILABLE",
    "DATABASE_AVAILABLE"
]
