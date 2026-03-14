"""Exa adapter for web search."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.base import DataSourceResult


class ExaAdapter:
    """Adapter for Exa search API."""
    
    def __init__(self):
        self.source_name = "Exa"
        self.source_type = "search"
        self.api_key = os.getenv("EXA_API_KEY", "")
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch data from Exa search."""
        try:
            search_query = query.get("search_query", query.get("company", ""))
            
            if not self.api_key:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="Exa API key not set (EXA_API_KEY)"
                )
            
            # Import from existing search module
            from search.search_engine import ExaSearchProvider
            
            provider = ExaSearchProvider(self.api_key)
            
            if not provider.is_available():
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="Exa API key not available"
                )
            
            results = provider.search(f"{search_query} 财务分析", max_results=10)
            
            data = []
            for r in results:
                data.append({
                    "type": "search",
                    "source": "Exa",
                    "title": r.title,
                    "content": r.content,
                    "url": r.url,
                    "source_type": r.source_type,
                    "credibility": str(r.credibility) if r.credibility else "unknown"
                })
            
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=data,
                success=True
            )
            
        except ImportError as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=f"Search module not available: {e}"
            )
        except Exception as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)
            )