"""
Production Environment Configuration

Overrides for production environment.
"""

from .base import BaseConfig, Environment, SecurityMode


class ProductionConfig(BaseConfig):
    """
    Production Configuration
    
    - Debug mode disabled
    - Full security (JWT + mTLS)
    - No hot reload
    - Production logging
    - All services enabled
    """
    
    # Override defaults for production
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    log_level: str = "INFO"
    api_reload: bool = False
    
    # Security: Full stack (JWT + mTLS)
    security_mode: SecurityMode = SecurityMode.PRODUCTION
    
    # Production UDS3 enabled
    uds3_enabled: bool = True
    
    # Production services (from existing config)
    postgres_host: str = "192.168.178.94"
    chroma_host: str = "192.168.178.94"
    neo4j_uri: str = "bolt://192.168.178.94:7687"
    couch_url: str = "http://192.168.178.94:32931"
    
    # Production Keycloak
    keycloak_url: str = "https://keycloak.vcc.local"  # Update to actual URL
    keycloak_realm: str = "vcc"
    keycloak_client_id: str = "clara-training-system"


# Singleton instance
prod_config = ProductionConfig()
