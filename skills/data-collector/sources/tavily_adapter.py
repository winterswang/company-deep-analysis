"""Tavily adapter for web search."""

import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
import logging
from typing import Any

from sources.base import BaseAdapter, DataSourceResult

logger = logging.getLogger(__name__)


class TavilyAdapter(BaseAdapter):
    """Adapter for Tavily search API."""
    
    def __init__(self):
        super().__init__()
        self.source_name = "Tavily"
        self.source_type = "search"
        self.api_key = os.getenv("TAVILY_API_KEY", "")
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch data from Tavily search."""
        try:
            search_query = query.get("search_query", query.get("company", ""))
            
            if not self.api_key:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="Tavily API key not set"
                )
            
            try:
                from tavily import TavilyClient
            except ImportError:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="tavily package not installed"
                )
            
            client = TavilyClient(api_key=self.api_key)
            results = client.search(query=f"{search_query} 财务分析 2024", max_results=10)
            
            data = []
            for item in results.get("results", []):
                data.append({
                    "type": "search",
                    "source": "Tavily",
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "url": item.get("url", ""),
                    "score": item.get("score", 0)
                })
            
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=data,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error fetching from Tavily: {e}")
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)
            )
