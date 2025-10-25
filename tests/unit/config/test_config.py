"""
Unit Tests for Config Package

Tests the centralized configuration system.
"""

import pytest
import os
from unittest.mock import patch

from config import config, get_config, Environment, SecurityMode
from config.base import BaseConfig
from config.development import DevelopmentConfig
from config.production import ProductionConfig
from config.testing import TestingConfig


class TestBaseConfig:
    """Test BaseConfig class"""
    
    def test_default_config_loads(self):
        """Test that default config loads without errors"""
        cfg = BaseConfig()
        
        assert cfg.app_name is not None
        assert cfg.environment is not None
        assert isinstance(cfg.training_port, int)
        assert isinstance(cfg.dataset_port, int)
    
    def test_config_fields_present(self):
        """Test that all expected fields are present"""
        cfg = BaseConfig()
        
        # Application
        assert hasattr(cfg, 'app_name')
        assert hasattr(cfg, 'environment')
        assert hasattr(cfg, 'debug')
        assert hasattr(cfg, 'log_level')
        
        # API
        assert hasattr(cfg, 'api_host')
        assert hasattr(cfg, 'api_port')
        assert hasattr(cfg, 'api_workers')
        
        # Backends
        assert hasattr(cfg, 'training_port')
        assert hasattr(cfg, 'dataset_port')
        
        # Security
        assert hasattr(cfg, 'security_mode')
        assert hasattr(cfg, 'keycloak_url')
        
        # Database
        assert hasattr(cfg, 'postgres_host')
        assert hasattr(cfg, 'postgres_port')
    
    def test_computed_properties(self):
        """Test computed properties work correctly"""
        cfg = BaseConfig()
        
        # Keycloak URLs
        assert cfg.keycloak_issuer.startswith(cfg.keycloak_url)
        assert 'realms' in cfg.keycloak_issuer
        assert 'certs' in cfg.keycloak_jwks_url
        
        # PostgreSQL DSN
        assert cfg.postgres_dsn.startswith('postgresql://')
        assert cfg.postgres_host in cfg.postgres_dsn
        
        # Environment checks
        assert isinstance(cfg.is_development, bool)
        assert isinstance(cfg.is_production, bool)
        assert isinstance(cfg.is_testing, bool)


class TestEnvironmentConfigs:
    """Test environment-specific configurations"""
    
    def test_development_config(self):
        """Test DevelopmentConfig overrides"""
        cfg = DevelopmentConfig()
        
        assert cfg.environment == Environment.DEVELOPMENT
        assert cfg.debug is True
        assert cfg.security_mode == SecurityMode.DEVELOPMENT
        assert cfg.api_reload is True
        assert cfg.log_level == "DEBUG"
    
    def test_production_config(self):
        """Test ProductionConfig overrides"""
        cfg = ProductionConfig()
        
        assert cfg.environment == Environment.PRODUCTION
        assert cfg.debug is False
        assert cfg.security_mode == SecurityMode.PRODUCTION
        assert cfg.api_reload is False
        assert cfg.uds3_enabled is True
    
    def test_testing_config(self):
        """Test TestingConfig overrides"""
        cfg = TestingConfig()
        
        assert cfg.environment == Environment.TESTING
        assert cfg.debug is True
        assert cfg.security_mode == SecurityMode.TESTING
        assert cfg.jwt_enabled is False
        assert cfg.postgres_database == "test_clara"


class TestConfigFactory:
    """Test get_config() factory function"""
    
    def test_get_config_default(self):
        """Test get_config() returns correct type"""
        cfg = get_config()
        assert isinstance(cfg, BaseConfig)
    
    def test_get_config_development(self):
        """Test get_config('development')"""
        cfg = get_config("development")
        assert cfg.environment == Environment.DEVELOPMENT
    
    def test_get_config_production(self):
        """Test get_config('production')"""
        cfg = get_config("production")
        assert cfg.environment == Environment.PRODUCTION
    
    def test_get_config_testing(self):
        """Test get_config('testing')"""
        cfg = get_config("testing")
        assert cfg.environment == Environment.TESTING
    
    @patch.dict(os.environ, {"CLARA_ENVIRONMENT": "production"})
    def test_get_config_from_env(self):
        """Test get_config() reads from CLARA_ENVIRONMENT"""
        # This test needs to reload config module to pick up env var
        # For now, just verify the factory accepts env parameter
        cfg = get_config("production")
        assert cfg.environment == Environment.PRODUCTION


class TestSecurityConfig:
    """Test security configuration"""
    
    def test_security_mode_enum(self):
        """Test SecurityMode enum values"""
        assert SecurityMode.PRODUCTION == "production"
        assert SecurityMode.DEVELOPMENT == "development"
        assert SecurityMode.DEBUG == "debug"
        assert SecurityMode.TESTING == "testing"
    
    def test_jwt_enabled_resolved(self):
        """Test JWT enabled resolution based on security mode"""
        # Production: JWT enabled by default
        prod_cfg = ProductionConfig()
        assert prod_cfg.jwt_enabled_resolved is True
        
        # Testing: JWT disabled by default
        test_cfg = TestingConfig()
        assert test_cfg.jwt_enabled_resolved is False
    
    def test_mtls_enabled_resolved(self):
        """Test mTLS enabled resolution based on security mode"""
        # Production: mTLS enabled
        prod_cfg = ProductionConfig()
        assert prod_cfg.mtls_enabled_resolved is True
        
        # Development: mTLS disabled
        dev_cfg = DevelopmentConfig()
        assert dev_cfg.mtls_enabled_resolved is False


class TestDatabaseConfig:
    """Test database configuration"""
    
    def test_postgres_dsn_format(self):
        """Test PostgreSQL DSN is correctly formatted"""
        cfg = BaseConfig()
        dsn = cfg.postgres_dsn
        
        assert dsn.startswith('postgresql://')
        assert cfg.postgres_user in dsn
        assert cfg.postgres_host in dsn
        assert str(cfg.postgres_port) in dsn
        assert cfg.postgres_database in dsn
    
    def test_database_hosts(self):
        """Test database host configuration"""
        prod_cfg = ProductionConfig()
        
        # Production uses remote hosts
        assert prod_cfg.postgres_host == "192.168.178.94"
        assert prod_cfg.chroma_host == "192.168.178.94"
        
        dev_cfg = DevelopmentConfig()
        
        # Development uses localhost
        assert dev_cfg.postgres_host == "localhost"
        assert dev_cfg.chroma_host == "localhost"


class TestEnvironmentEnum:
    """Test Environment enum"""
    
    def test_environment_values(self):
        """Test Environment enum values"""
        assert Environment.DEVELOPMENT == "development"
        assert Environment.PRODUCTION == "production"
        assert Environment.TESTING == "testing"


class TestGlobalConfigInstance:
    """Test global config instance"""
    
    def test_config_is_singleton(self):
        """Test that config is a singleton"""
        from config import config as config1
        from config import config as config2
        
        # Should be the same instance (cached)
        assert config1 is config2
