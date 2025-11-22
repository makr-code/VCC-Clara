"""
Base Configuration using Pydantic Settings

Centralized configuration management for all Clara services.
"""

from typing import Optional, List
from enum import Enum
from pathlib import Path
from functools import lru_cache

try:
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback for older pydantic versions
    try:
        from pydantic import BaseSettings, Field
        SettingsConfigDict = None
        PYDANTIC_AVAILABLE = True
    except ImportError:
        PYDANTIC_AVAILABLE = False
        BaseSettings = object
        Field = lambda *args, **kwargs: kwargs.get('default')


class Environment(str, Enum):
    """Environment Types"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class SecurityMode(str, Enum):
    """Security Modes"""
    PRODUCTION = "production"   # Full security (JWT + mTLS)
    DEVELOPMENT = "development" # JWT only, no mTLS
    DEBUG = "debug"            # No security (mock user)
    TESTING = "testing"        # Mock JWT for tests


if PYDANTIC_AVAILABLE:
    class BaseConfig(BaseSettings):
        """
        Base Configuration Class
        
        Reads from environment variables with CLARA_ prefix.
        Can be overridden by .env files in project root.
        """
        
        # ===== Application Settings =====
        app_name: str = Field(default="Clara Training System", alias="CLARA_APP_NAME")
        environment: Environment = Field(default=Environment.DEVELOPMENT, alias="CLARA_ENVIRONMENT")
        debug: bool = Field(default=False, alias="CLARA_DEBUG")
        log_level: str = Field(default="INFO", alias="CLARA_LOG_LEVEL")
        
        # ===== API Settings =====
        api_host: str = Field(default="0.0.0.0", alias="CLARA_API_HOST")
        api_port: int = Field(default=8000, alias="CLARA_API_PORT")
        api_workers: int = Field(default=4, alias="CLARA_API_WORKERS")
        api_reload: bool = Field(default=False, alias="CLARA_API_RELOAD")
        
        # ===== Backend Service Ports =====
        training_port: int = Field(default=45680, alias="CLARA_TRAINING_PORT")
        dataset_port: int = Field(default=45681, alias="CLARA_DATASET_PORT")
        
        # ===== Worker Configuration =====
        max_concurrent_jobs: int = Field(default=2, alias="CLARA_MAX_CONCURRENT_JOBS")
        worker_timeout: int = Field(default=3600, alias="CLARA_WORKER_TIMEOUT")
        
        # ===== Security Settings =====
        security_mode: SecurityMode = Field(default=SecurityMode.PRODUCTION, alias="CLARA_SECURITY_MODE")
        jwt_enabled: Optional[bool] = Field(default=None, alias="CLARA_JWT_ENABLED")
        mtls_enabled: Optional[bool] = Field(default=None, alias="CLARA_MTLS_ENABLED")
        
        # ===== Keycloak Settings =====
        keycloak_url: str = Field(default="http://localhost:8080", alias="KEYCLOAK_URL")
        keycloak_realm: str = Field(default="vcc", alias="KEYCLOAK_REALM")
        keycloak_client_id: str = Field(default="clara-training-system", alias="KEYCLOAK_CLIENT_ID")
        jwt_algorithm: str = Field(default="RS256", alias="JWT_ALGORITHM")
        
        # ===== Debug Mode Settings =====
        debug_user_id: str = Field(default="debug-user", alias="DEBUG_USER_ID")
        debug_user_email: str = Field(default="debug@clara.local", alias="DEBUG_USER_EMAIL")
        debug_user_roles: str = Field(default="admin,trainer", alias="DEBUG_USER_ROLES")
        
        # ===== Database Settings (UDS3) =====
        # PostgreSQL
        postgres_host: str = Field(default="192.168.178.94", alias="POSTGRES_HOST")
        postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
        postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
        postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
        postgres_database: str = Field(default="postgres", alias="POSTGRES_DATABASE")
        postgres_schema: str = Field(default="public", alias="POSTGRES_SCHEMA")
        
        # ChromaDB
        chroma_host: str = Field(default="192.168.178.94", alias="CHROMA_HOST")
        chroma_port: int = Field(default=8000, alias="CHROMA_PORT")
        
        # Neo4j
        neo4j_uri: str = Field(default="bolt://192.168.178.94:7687", alias="NEO4J_URI")
        neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
        neo4j_password: str = Field(default="password", alias="NEO4J_PASSWORD")
        
        # CouchDB
        couch_url: str = Field(default="http://192.168.178.94:32931", alias="COUCH_URL")
        couch_user: str = Field(default="admin", alias="COUCH_USER")
        couch_password: str = Field(default="admin", alias="COUCH_PASSWORD")
        
        # ===== UDS3 Settings =====
        uds3_enabled: bool = Field(default=True, alias="UDS3_ENABLED")
        
        # ===== Streaming Settings =====
        streaming_enabled: bool = Field(default=True, alias="STREAMING_ENABLED")
        streaming_batch_size: int = Field(default=100, ge=10, le=1000, alias="STREAMING_BATCH_SIZE")
        
        # ===== File Paths =====
        project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent)
        data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "data")
        models_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "models")
        logs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "logs")
        
        # ===== Model Configuration =====
        # Pydantic v2
        if SettingsConfigDict is not None:
            model_config = SettingsConfigDict(
                env_file=".env",
                env_file_encoding="utf-8",
                case_sensitive=False,
                extra="ignore"
            )
        else:
            # Pydantic v1
            class Config:
                env_file = ".env"
                env_file_encoding = "utf-8"
                case_sensitive = False
                extra = "ignore"
        
        # ===== Computed Properties =====
        @property
        def is_development(self) -> bool:
            """Check if running in development mode"""
            return self.environment == Environment.DEVELOPMENT
        
        @property
        def is_production(self) -> bool:
            """Check if running in production mode"""
            return self.environment == Environment.PRODUCTION
        
        @property
        def is_testing(self) -> bool:
            """Check if running in testing mode"""
            return self.environment == Environment.TESTING
        
        @property
        def keycloak_issuer(self) -> str:
            """Get Keycloak issuer URL"""
            return f"{self.keycloak_url}/realms/{self.keycloak_realm}"
        
        @property
        def keycloak_jwks_url(self) -> str:
            """Get Keycloak JWKS URL"""
            return f"{self.keycloak_issuer}/protocol/openid-connect/certs"
        
        @property
        def postgres_dsn(self) -> str:
            """Get PostgreSQL DSN"""
            return (
                f"postgresql://{self.postgres_user}:{self.postgres_password}@"
                f"{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            )
        
        @property
        def debug_user_roles_list(self) -> List[str]:
            """Get debug user roles as list"""
            return [r.strip() for r in self.debug_user_roles.split(",")]
        
        @property
        def jwt_enabled_resolved(self) -> bool:
            """Resolve JWT enabled status based on security mode"""
            if self.jwt_enabled is not None:
                return self.jwt_enabled
            return self.security_mode != SecurityMode.DEBUG
        
        @property
        def mtls_enabled_resolved(self) -> bool:
            """Resolve mTLS enabled status based on security mode"""
            if self.mtls_enabled is not None:
                return self.mtls_enabled
            return self.security_mode == SecurityMode.PRODUCTION

else:
    # Fallback for when pydantic is not available
    class BaseConfig:
        """Fallback configuration without pydantic"""
        def __init__(self):
            import os
            self.app_name = os.getenv("CLARA_APP_NAME", "Clara Training System")
            self.environment = Environment.DEVELOPMENT
            self.debug = os.getenv("CLARA_DEBUG", "false").lower() == "true"
            self.log_level = os.getenv("CLARA_LOG_LEVEL", "INFO")
            # Add other fields as needed
            print("⚠️ Pydantic not available, using fallback config")


# ===== Global Config Factory =====
@lru_cache(maxsize=1)
def get_config() -> BaseConfig:
    """
    Get cached configuration instance.
    
    Returns:
        BaseConfig: Cached configuration object
    """
    return BaseConfig()


# ===== Convenience Export =====
config = get_config()
