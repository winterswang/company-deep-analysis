"""Base adapter for data sources."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class DataSourceResult:
    """Result from a data source."""
    
    source_name: str
    source_type: str  # api, crawler, search
    data: list[dict]
    success: bool
    error: str | None = None
    
    @property
    def quality_level(self) -> str:
        """Return quality level based on source type."""
        levels = {
            "api": "P0",      # AkShare
            "crawler": "P0",  # Official filings
            "search": "P2",   # Web search
        }
        return levels.get(self.source_type, "P3")


class BaseAdapter(ABC):
    """Base class for data source adapters."""
    
    def __init__(self):
        self.source_name = self.__class__.__name__.replace("Adapter", "").lower()
    
    @abstractmethod
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch data based on query."""
        pass
    
    def get_source_name(self) -> str:
        return self.source_name
