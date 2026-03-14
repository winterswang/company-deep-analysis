"""Data source adapters."""

# Import adapters when implemented
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sources.base import BaseAdapter, DataSourceResult


__all__ = [
    "BaseAdapter",
    "DataSourceResult",
]