"""
Dataset Backend Package

Microservice für Dataset-Vorbereitung und -Verwaltung
"""

from .app import app
from .manager import DatasetManager
from .models import Dataset, DatasetStatus, ExportFormat

__version__ = "1.0.0"

__all__ = [
    "app",
    "DatasetManager",
    "Dataset",
    "DatasetStatus",
    "ExportFormat"
]
