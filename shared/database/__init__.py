"""
Database Package

UDS3 Integration and Database Utilities
"""

# Try to import UDS3 Dataset Search (optional)
try:
    from .dataset_search import (
        DatasetSearchAPI,
        DatasetSearchQuery,
        DatasetDocument,
        UDS3_AVAILABLE
    )
    UDS3_SEARCH_AVAILABLE = True
except ImportError:
    DatasetSearchAPI = None
    DatasetSearchQuery = None
    DatasetDocument = None
    UDS3_AVAILABLE = False
    UDS3_SEARCH_AVAILABLE = False

__all__ = [
    "DatasetSearchAPI",
    "DatasetSearchQuery",
    "DatasetDocument",
    "UDS3_AVAILABLE",
    "UDS3_SEARCH_AVAILABLE"
]
