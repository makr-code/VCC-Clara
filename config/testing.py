"""
Testing Environment Configuration

Overrides for testing environment.
"""

from pathlib import Path
from .base import BaseConfig, Environment, SecurityMode


class TestingConfig(BaseConfig):
    """
    Testing Configuration
    
    - Debug mode enabled
    - Mock security (no real JWT/mTLS)
    - In-memory databases where possible
    - Test-specific paths
    """
    
    # Override defaults for testing
    environment: Environment = Environment.TESTING
    debug: bool = True
    log_level: str = "DEBUG"
    api_reload: bool = False  # No reload during tests
    
    # Security: Testing mode (mock JWT)
    security_mode: SecurityMode = SecurityMode.TESTING
    jwt_enabled: bool = False  # Use mock security
    mtls_enabled: bool = False
    
    # Test UDS3 (mock backends)
    uds3_enabled: bool = False
    
    # Test database connections (mock or in-memory)
    postgres_host: str = "localhost"
    postgres_database: str = "test_clara"
    chroma_host: str = "localhost"
    neo4j_uri: str = "bolt://localhost:7687"
    couch_url: str = "http://localhost:5984"
    
    # Test-specific paths
    data_dir: Path = Path(__file__).parent.parent / "tests" / "data"
    models_dir: Path = Path(__file__).parent.parent / "tests" / "models"
    logs_dir: Path = Path(__file__).parent.parent / "tests" / "logs"
    
    # Test worker configuration (limited resources)
    max_concurrent_jobs: int = 1
    worker_timeout: int = 60  # Shorter timeout for tests


# Singleton instance
test_config = TestingConfig()
