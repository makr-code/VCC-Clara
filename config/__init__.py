"""
Configuration Package

Environment-based configuration management using Pydantic Settings.

Usage:
    # Default config (auto-detects from CLARA_ENVIRONMENT)
    from config import config
    print(config.api_port)
    
    # Specific environment
    from config import get_config
    config = get_config("production")
    
    # Environment-specific imports
    from config.development import dev_config
    from config.production import prod_config
    from config.testing import test_config
"""

import os
from typing import Union
from .base import BaseConfig, Environment, SecurityMode, get_config as get_base_config


def get_config(env: str = None) -> BaseConfig:
    """
    Get configuration for specific environment.
    
    Args:
        env: Environment name ("development", "production", "testing")
             If None, reads from CLARA_ENVIRONMENT (default: development)
    
    Returns:
        BaseConfig: Configuration instance for the specified environment
    
    Examples:
        >>> config = get_config()  # Auto-detect from env var
        >>> config = get_config("production")
        >>> config = get_config("testing")
    """
    if env is None:
        env = os.environ.get("CLARA_ENVIRONMENT", "development").lower()
    
    env = env.lower()
    
    if env == "production":
        from .production import prod_config
        return prod_config
    elif env == "testing":
        from .testing import test_config
        return test_config
    else:  # development (default)
        from .development import dev_config
        return dev_config


# ===== Global Config Instance =====
# Auto-loads based on CLARA_ENVIRONMENT
config = get_config()


# ===== Exports =====
__all__ = [
    # Main config
    "config",
    "get_config",
    
    # Base classes
    "BaseConfig",
    "Environment",
    "SecurityMode",
    
    # Environment-specific configs
    "dev_config",
    "prod_config",
    "test_config",
]


# Re-export environment configs for convenience
from .development import dev_config
from .production import prod_config
from .testing import test_config
