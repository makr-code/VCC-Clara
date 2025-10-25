"""
Security Configuration Models

DEPRECATED: This module is deprecated. Use config.base instead.

For backward compatibility, this module re-exports from config.
"""

import logging

logger = logging.getLogger(__name__)

# Re-export from centralized config
try:
    from config import config, SecurityMode
    
    # Backward compatibility wrapper
    class SecurityConfig:
        """
        DEPRECATED: Use config.config instead.
        
        This class is kept for backward compatibility.
        """
        
        def __init__(self):
            logger.warning("⚠️ SecurityConfig is deprecated. Use 'from config import config' instead.")
            
            # Map config values to old interface
            self.mode = config.security_mode
            self.jwt_enabled = config.jwt_enabled_resolved
            self.mtls_enabled = config.mtls_enabled_resolved
            
            self.keycloak_url = config.keycloak_url
            self.keycloak_realm = config.keycloak_realm
            self.keycloak_client_id = config.keycloak_client_id
            self.jwt_algorithm = config.jwt_algorithm
            
            self.issuer = config.keycloak_issuer
            self.jwks_url = config.keycloak_jwks_url
            
            self.debug_user_id = config.debug_user_id
            self.debug_user_email = config.debug_user_email
            self.debug_user_roles = config.debug_user_roles_list
        
        @staticmethod
        def _parse_bool(value, default=False):
            """DEPRECATED: Use config.config instead"""
            if value is None:
                return default
            return value.lower() in ("true", "1", "yes", "on")
        
        def _log_config(self):
            """DEPRECATED: Use config.config instead"""
            pass
    
    # For backward compatibility
    def get_security_config() -> SecurityConfig:
        """DEPRECATED: Use 'from config import config' instead"""
        return SecurityConfig()
    
    security_config = get_security_config()

except ImportError:
    # Fallback to old implementation if config package not available
    logger.error("❌ Config package not found. Using fallback SecurityConfig.")
    
    import os
    from enum import Enum
    from functools import lru_cache
    
    class SecurityMode(str, Enum):
        """Security Modes"""
        PRODUCTION = "production"
        DEVELOPMENT = "development"
        DEBUG = "debug"
        TESTING = "testing"
    
    class SecurityConfig:
        """Fallback SecurityConfig"""
        def __init__(self):
            self.mode = SecurityMode(
                os.environ.get("CLARA_SECURITY_MODE", "production").lower()
            )
            self.jwt_enabled = os.environ.get("CLARA_JWT_ENABLED", "true").lower() == "true"
            self.mtls_enabled = os.environ.get("CLARA_MTLS_ENABLED", "false").lower() == "true"
            self.keycloak_url = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
            self.keycloak_realm = os.environ.get("KEYCLOAK_REALM", "vcc")
            self.keycloak_client_id = os.environ.get("KEYCLOAK_CLIENT_ID", "clara-training-system")
            self.jwt_algorithm = os.environ.get("JWT_ALGORITHM", "RS256")
            self.issuer = f"{self.keycloak_url}/realms/{self.keycloak_realm}"
            self.jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
            self.debug_user_id = os.environ.get("DEBUG_USER_ID", "debug-user")
            self.debug_user_email = os.environ.get("DEBUG_USER_EMAIL", "debug@clara.local")
            self.debug_user_roles = os.environ.get("DEBUG_USER_ROLES", "admin,trainer").split(",")
        
        @staticmethod
        def _parse_bool(value, default=False):
            if value is None:
                return default
            return value.lower() in ("true", "1", "yes", "on")
        
        def _log_config(self):
            pass
    
    @lru_cache(maxsize=1)
    def get_security_config() -> SecurityConfig:
        return SecurityConfig()
    
    security_config = get_security_config()

