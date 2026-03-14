"""Xueqiu (雪球) adapter for financial data and discussions."""

import sys
import os
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from sources.base import DataSourceResult


class XueqiuAdapter:
    """Adapter for Xueqiu (雪球) data."""
    
    def __init__(self):
        self.source_name = "雪球"
        self.source_type = "crawler"
        self.xueqiu_project = os.path.join(project_root, "..", "..", "..", "xueqiu-crawler")
    
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
            
            # Check if xueqiu-crawler project exists
            if not os.path.exists(self.xueqiu_project):
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error=f"Xueqiu crawler project not found at {self.xueqiu_project}"
                )
            
            # Add xueqiu-crawler to path
            sys.path.insert(0, os.path.join(self.xueqiu_project, "scripts"))
            
            try:
                from crawler import XueqiuCrawler
                
                # Create crawler instance
                crawler = XueqiuCrawler()
                
                # Get some popular Xueqiu users to search
                # For now, just return a note that crawler needs specific user config
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[{
                        "type": "note",
                        "source": "雪球",
                        "content": "Xueqiu crawler requires specific user configuration. Please configure users in xueqiu-crawler project first.",
                        "ticker": ticker or company
                    }],
                    success=True
                )
                
            except ImportError as e:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error=f"Cannot import XueqiuCrawler: {e}"
                )
            
        except Exception as e:
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)
            )
