"""
Logging-Konfiguration für VerwLLM
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str, log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Richte Logger ein.
    
    Args:
        name: Name des Loggers
        log_level: Log-Level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional: Pfad zur Log-Datei
        
    Returns:
        logging.Logger: Konfigurierter Logger
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Verhindere doppelte Handler
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
