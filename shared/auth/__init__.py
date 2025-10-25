"""
Auth Package

JWT Middleware and Security Configuration
"""

from .models import SecurityMode, SecurityConfig, security_config
from .middleware import JWTMiddleware, jwt_middleware
from .utils import (
    get_current_user_id,
    get_current_user_email,
    get_current_user_roles,
    has_role,
    has_any_role,
    has_all_roles
)

__all__ = [
    # Models
    "SecurityMode",
    "SecurityConfig",
    "security_config",
    
    # Middleware
    "JWTMiddleware",
    "jwt_middleware",
    
    # Utils
    "get_current_user_id",
    "get_current_user_email",
    "get_current_user_roles",
    "has_role",
    "has_any_role",
    "has_all_roles"
]
