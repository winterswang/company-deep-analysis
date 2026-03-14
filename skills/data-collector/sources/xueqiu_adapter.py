"""Xueqiu (雪球) adapter for financial data and discussions."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources.base import DataSourceResult


class XueqiuAdapter:
    """Adapter for Xueqiu (雪球) data."""
    
    def __init__(self):
        self.source_name = "雪球"
        self.source_type = "crawler"
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch data from Xueqiu."""
        try:
            company = query.get("company", "")
            ticker = query.get("ticker", "")
            
            if not company and not ticker:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="No company or ticker provided"
                )
            
            # Import from existing search module
            from search.search_engine import XueqiuProvider
            
            provider = XueqiuProvider()
            
            if not provider.is_available():
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="Xueqiu crawler not available"
                )
            
            # Search for company related content
            search_term = ticker if ticker else company
            results = provider.search(f"{search_term} 财务", max_results=10)
            
            data = []
            for r in results:
                data.append({
                    "type": "xueqiu",
                    "source": "雪球",
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