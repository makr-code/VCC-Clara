#!/usr/bin/env python3
"""
JWT Middleware for CLARA Training System
Environment-Variable based Security Configuration

Security Modes (via CLARA_SECURITY_MODE):
- "production": Full JWT + mTLS validation (default)
- "development": JWT validation, no mTLS
- "debug": No security, mock user (WARNING: Development only!)
- "testing": Mock JWT validation for tests

Author: VCC Team
Date: 2024-10-24
"""

import os
import logging
from typing import Optional, List, Dict, Any, Callable
from functools import lru_cache
from enum import Enum

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Conditional imports - graceful degradation
try:
    import jwt
    import requests
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None
    requests = None

try:
    from cryptography.hazmat.primitives import serialization
    from jose import jwk as jose_jwk
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# Security Configuration
# ============================================================================

class SecurityMode(str, Enum):
    """Security Modes"""
    PRODUCTION = "production"   # Full security (JWT + mTLS)
    DEVELOPMENT = "development" # JWT only, no mTLS
    DEBUG = "debug"            # No security (mock user)
    TESTING = "testing"        # Mock JWT for tests


class SecurityConfig:
    """
    Security Configuration from Environment Variables
    
    Environment Variables:
    - CLARA_SECURITY_MODE: production|development|debug|testing (default: production)
    - CLARA_JWT_ENABLED: true|false (default: true, overrides mode)
    - CLARA_MTLS_ENABLED: true|false (default: false)
    - KEYCLOAK_URL: Keycloak URL (default: http://localhost:8080)
    - KEYCLOAK_REALM: Realm name (default: vcc)
    - KEYCLOAK_CLIENT_ID: Client ID (default: clara-training-system)
    - JWT_ALGORITHM: Algorithm (default: RS256)
    - DEBUG_USER_ID: User ID for debug mode (default: debug-user)
    - DEBUG_USER_EMAIL: User email for debug mode (default: debug@clara.local)
    - DEBUG_USER_ROLES: Comma-separated roles (default: admin,trainer)
    """
    
    def __init__(self):
        # Security Mode
        self.mode = SecurityMode(
            os.environ.get("CLARA_SECURITY_MODE", "production").lower()
        )
        
        # JWT Configuration
        self.jwt_enabled = self._parse_bool(
            os.environ.get("CLARA_JWT_ENABLED"),
            default=(self.mode != SecurityMode.DEBUG)
        )
        
        # mTLS Configuration
        self.mtls_enabled = self._parse_bool(
            os.environ.get("CLARA_MTLS_ENABLED"),
            default=(self.mode == SecurityMode.PRODUCTION)
        )
        
        # Keycloak Configuration
        self.keycloak_url = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
        self.keycloak_realm = os.environ.get("KEYCLOAK_REALM", "vcc")
        self.keycloak_client_id = os.environ.get("KEYCLOAK_CLIENT_ID", "clara-training-system")
        self.jwt_algorithm = os.environ.get("JWT_ALGORITHM", "RS256")
        
        # Computed values
        self.issuer = f"{self.keycloak_url}/realms/{self.keycloak_realm}"
        self.jwks_url = f"{self.issuer}/protocol/openid-connect/certs"
        
        # Debug Mode Configuration
        self.debug_user_id = os.environ.get("DEBUG_USER_ID", "debug-user")
        self.debug_user_email = os.environ.get("DEBUG_USER_EMAIL", "debug@clara.local")
        self.debug_user_roles = os.environ.get("DEBUG_USER_ROLES", "admin,trainer").split(",")
        
        # Log configuration
        self._log_config()
    
    @staticmethod
    def _parse_bool(value: Optional[str], default: bool = False) -> bool:
        """Parse boolean from string"""
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    def _log_config(self):
        """Log security configuration"""
        logger.info("=" * 60)
        logger.info("CLARA Security Configuration")
        logger.info("=" * 60)
        logger.info(f"Security Mode: {self.mode.value.upper()}")
        logger.info(f"JWT Enabled: {self.jwt_enabled}")
        logger.info(f"mTLS Enabled: {self.mtls_enabled}")
        
        if self.jwt_enabled:
            logger.info(f"Keycloak URL: {self.keycloak_url}")
            logger.info(f"Realm: {self.keycloak_realm}")
            logger.info(f"Client ID: {self.keycloak_client_id}")
        
        if self.mode == SecurityMode.DEBUG:
            logger.warning("⚠️  DEBUG MODE ACTIVE - NO SECURITY ENFORCEMENT!")
            logger.warning(f"   Debug User: {self.debug_user_email}")
            logger.warning(f"   Debug Roles: {self.debug_user_roles}")
        
        logger.info("=" * 60)


# Global config instance
security_config = SecurityConfig()


# ============================================================================
# JWT Middleware
# ============================================================================

class JWTMiddleware:
    """
    JWT Middleware with Environment-based Security Mode
    
    Modes:
    - production: Full JWT validation with Keycloak
    - development: JWT validation, relaxed settings
    - debug: Mock user, no validation (WARNING: Development only!)
    - testing: Mock validation for unit tests
    """
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or security_config
        self.security = HTTPBearer(auto_error=False)  # Don't auto-raise on missing token
        self._public_key_cache: Optional[str] = None
        
        # Check dependencies
        if self.config.jwt_enabled and not JWT_AVAILABLE:
            logger.error("JWT enabled but PyJWT not installed! Run: pip install PyJWT requests")
            logger.warning("Falling back to DEBUG mode")
            self.config.mode = SecurityMode.DEBUG
            self.config.jwt_enabled = False
    
    @lru_cache(maxsize=1)
    def get_public_key(self) -> str:
        """
        Fetch Keycloak Public Key for JWT validation
        
        Cached for performance (updates every ~1 hour in production)
        """
        if not self.config.jwt_enabled:
            return ""
        
        if self.config.mode == SecurityMode.TESTING:
            # Mock key for testing
            return "mock-public-key"
        
        try:
            logger.debug(f"Fetching JWKS from: {self.config.jwks_url}")
            response = requests.get(self.config.jwks_url, timeout=5)
            response.raise_for_status()
            
            jwks = response.json()
            
            # Find RS256 signing key
            for key in jwks.get("keys", []):
                if key.get("alg") == self.config.jwt_algorithm and key.get("use") == "sig":
                    return self._jwk_to_pem(key)
            
            raise ValueError(f"No {self.config.jwt_algorithm} signing key found in JWKS")
        
        except Exception as e:
            logger.error(f"Failed to fetch Keycloak public key: {e}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )
    
    @staticmethod
    def _jwk_to_pem(jwk_dict: dict) -> str:
        """Convert JWK to PEM format"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography package required for JWK conversion")
        
        try:
            public_key = jose_jwk.construct(jwk_dict).public_key()
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode()
        except Exception as e:
            logger.error(f"JWK to PEM conversion failed: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT Token
        
        Args:
            token: JWT token string
            
        Returns:
            dict: Token payload (claims)
            
        Raises:
            HTTPException: On validation failure
        """
        # Debug mode: Return mock claims
        if self.config.mode == SecurityMode.DEBUG:
            return self._get_debug_claims()
        
        # Testing mode: Return mock claims
        if self.config.mode == SecurityMode.TESTING:
            return self._get_test_claims(token)
        
        # Production/Development: Validate token
        try:
            public_key = self.get_public_key()
            
            payload = jwt.decode(
                token,
                public_key,
                algorithms=[self.config.jwt_algorithm],
                issuer=self.config.issuer,
                audience=self.config.keycloak_client_id,
                options={
                    "verify_exp": True,
                    "verify_iss": True,
                    "verify_aud": True
                }
            )
            
            logger.debug(f"Token verified for user: {payload.get('email', 'unknown')}")
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise HTTPException(status_code=401, detail="Token expired")
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Token verification failed")
    
    def _get_debug_claims(self) -> Dict[str, Any]:
        """Get mock claims for debug mode"""
        return {
            "sub": self.config.debug_user_id,
            "email": self.config.debug_user_email,
            "preferred_username": "debug",
            "realm_access": {
                "roles": self.config.debug_user_roles
            },
            "iss": self.config.issuer,
            "aud": self.config.keycloak_client_id,
            "exp": 9999999999,  # Far future
            "iat": 1000000000,
            "debug_mode": True
        }
    
    def _get_test_claims(self, token: str) -> Dict[str, Any]:
        """Get mock claims for testing mode"""
        # Parse token payload without verification
        try:
            # Simple base64 decode of payload (for testing only!)
            import base64
            import json
            
            parts = token.split(".")
            if len(parts) == 3:
                payload_encoded = parts[1]
                # Add padding if needed
                padding = 4 - len(payload_encoded) % 4
                if padding != 4:
                    payload_encoded += "=" * padding
                
                payload = json.loads(base64.urlsafe_b64decode(payload_encoded))
                return payload
        except Exception:
            pass
        
        # Fallback to default test claims
        return {
            "sub": "test-user",
            "email": "test@clara.local",
            "preferred_username": "test",
            "realm_access": {
                "roles": ["admin"]
            },
            "test_mode": True
        }
    
    async def get_current_user(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(lambda: None)
    ) -> Dict[str, Any]:
        """
        Get current user from JWT token
        
        Dependency for FastAPI endpoints
        
        Usage:
            @app.get("/protected")
            async def protected_route(user: dict = Depends(jwt_middleware.get_current_user)):
                return {"user": user["email"]}
        """
        # Debug mode: Always return mock user
        if self.config.mode == SecurityMode.DEBUG:
            logger.debug("DEBUG MODE: Using mock user")
            return self._get_debug_claims()
        
        # Extract Authorization header
        credentials = await self.security(request)
        
        if not credentials:
            logger.warning("Missing Authorization header")
            raise HTTPException(
                status_code=401,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = credentials.credentials
        
        # Verify and return claims
        return self.verify_token(token)
    
    def require_roles(
        self,
        required_roles: List[str],
        require_all: bool = False
    ) -> Callable:
        """
        Create dependency for role-based access control
        
        Args:
            required_roles: List of allowed roles (e.g., ["admin", "trainer"])
            require_all: If True, user must have ALL roles. If False, ANY role is sufficient.
        
        Returns:
            FastAPI dependency function
        
        Usage:
            @app.post("/api/training/jobs")
            async def create_job(
                request: JobRequest,
                user: dict = Depends(jwt_middleware.require_roles(["admin", "trainer"]))
            ):
                # User has admin OR trainer role
                ...
        """
        async def dependency(
            user_claims: Dict[str, Any] = Depends(self.get_current_user)
        ) -> Dict[str, Any]:
            """RBAC Dependency"""
            
            # Debug mode: Skip role check
            if self.config.mode == SecurityMode.DEBUG:
                logger.debug(f"DEBUG MODE: Skipping role check for roles: {required_roles}")
                return user_claims
            
            # Extract user roles
            user_roles = user_claims.get("realm_access", {}).get("roles", [])
            
            # Check roles
            if require_all:
                # User must have ALL required roles
                if not all(role in user_roles for role in required_roles):
                    logger.warning(
                        f"User {user_claims.get('email')} missing required roles. "
                        f"Required (all): {required_roles}, Has: {user_roles}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Insufficient permissions. Required roles (all): {required_roles}"
                    )
            else:
                # User must have ANY required role
                if not any(role in user_roles for role in required_roles):
                    logger.warning(
                        f"User {user_claims.get('email')} has no required roles. "
                        f"Required (any): {required_roles}, Has: {user_roles}"
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Insufficient permissions. Required roles (any): {required_roles}"
                    )
            
            logger.debug(f"User {user_claims.get('email')} authorized with roles: {user_roles}")
            return user_claims
        
        return dependency
    
    def optional_auth(self) -> Callable:
        """
        Optional authentication dependency
        
        Returns user claims if token present, None otherwise
        
        Usage:
            @app.get("/api/public-or-private")
            async def route(user: Optional[dict] = Depends(jwt_middleware.optional_auth())):
                if user:
                    return {"message": f"Hello {user['email']}"}
                else:
                    return {"message": "Hello anonymous"}
        """
        async def dependency(request: Request) -> Optional[Dict[str, Any]]:
            """Optional Auth Dependency"""
            
            # Debug mode: Always return mock user
            if self.config.mode == SecurityMode.DEBUG:
                return self._get_debug_claims()
            
            # Try to get credentials
            credentials = await self.security(request)
            
            if not credentials:
                return None
            
            try:
                return self.verify_token(credentials.credentials)
            except HTTPException:
                # Token invalid, return None instead of raising
                return None
        
        return dependency


# ============================================================================
# Global Middleware Instance
# ============================================================================

jwt_middleware = JWTMiddleware()


# ============================================================================
# Convenience Functions
# ============================================================================

def get_current_user_id(user_claims: Dict[str, Any]) -> str:
    """Extract user ID from claims"""
    return user_claims.get("sub", "unknown")


def get_current_user_email(user_claims: Dict[str, Any]) -> str:
    """Extract user email from claims"""
    return user_claims.get("email", "unknown@unknown.local")


def get_current_user_roles(user_claims: Dict[str, Any]) -> List[str]:
    """Extract user roles from claims"""
    return user_claims.get("realm_access", {}).get("roles", [])


def has_role(user_claims: Dict[str, Any], role: str) -> bool:
    """Check if user has specific role"""
    return role in get_current_user_roles(user_claims)


def has_any_role(user_claims: Dict[str, Any], roles: List[str]) -> bool:
    """Check if user has any of the specified roles"""
    user_roles = get_current_user_roles(user_claims)
    return any(role in user_roles for role in roles)


def has_all_roles(user_claims: Dict[str, Any], roles: List[str]) -> bool:
    """Check if user has all of the specified roles"""
    user_roles = get_current_user_roles(user_claims)
    return all(role in user_roles for role in roles)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    Example: Test JWT Middleware in different modes
    
    Run with:
        # Production mode (requires Keycloak)
        python shared/jwt_middleware.py
        
        # Debug mode (no security)
        CLARA_SECURITY_MODE=debug python shared/jwt_middleware.py
        
        # Development mode (JWT validation only)
        CLARA_SECURITY_MODE=development python shared/jwt_middleware.py
    """
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test configuration
    print("\n" + "=" * 60)
    print("JWT Middleware Configuration Test")
    print("=" * 60)
    print(f"Mode: {security_config.mode.value}")
    print(f"JWT Enabled: {security_config.jwt_enabled}")
    print(f"mTLS Enabled: {security_config.mtls_enabled}")
    
    if security_config.mode == SecurityMode.DEBUG:
        print("\nDebug User Claims:")
        middleware = JWTMiddleware()
        claims = middleware._get_debug_claims()
        import json
        print(json.dumps(claims, indent=2))
    
    print("\n" + "=" * 60)
    print("Set CLARA_SECURITY_MODE environment variable to change mode:")
    print("  export CLARA_SECURITY_MODE=debug       # No security (development)")
    print("  export CLARA_SECURITY_MODE=development # JWT only")
    print("  export CLARA_SECURITY_MODE=production  # Full security (JWT + mTLS)")
    print("=" * 60)
