"""
Development Environment Configuration

Overrides for development environment.
"""

from .base import BaseConfig, Environment, SecurityMode


class DevelopmentConfig(BaseConfig):
    """
    Development Configuration
    
    - Debug mode enabled
    - JWT authentication enabled (Keycloak)
    - No mTLS required
    - Hot reload enabled
    - Verbose logging
    """
    
    # Override defaults for development
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = True
    log_level: str = "DEBUG"
    api_reload: bool = True
    
    # Security: JWT only, no mTLS
    security_mode: SecurityMode = SecurityMode.DEVELOPMENT
    
    # Development UDS3 (local or mock)
    uds3_enabled: bool = False  # Can be overridden via env var
    
    # Local Keycloak (if running)
    keycloak_url: str = "http://localhost:8080"
    
    # Local databases (if available)
    postgres_host: str = "localhost"
    chroma_host: str = "localhost"
    neo4j_uri: str = "bolt://localhost:7687"
    couch_url: str = "http://localhost:5984"


# Singleton instance
dev_config = DevelopmentConfig()
