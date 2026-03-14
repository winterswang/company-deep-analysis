"""AkShare adapter for financial data."""

import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Any

from sources.base import BaseAdapter, DataSourceResult

logger = logging.getLogger(__name__)


class AkShareAdapter(BaseAdapter):
    """Adapter for AkShare financial data API."""
    
    def __init__(self):
        super().__init__()
        self.source_name = "AkShare"
        self.source_type = "api"
    
    async def fetch(self, query: dict) -> DataSourceResult:
        """Fetch financial data from AkShare."""
        try:
            company = query.get("company", "")
            ticker = query.get("ticker", "")
            market = query.get("market", "cn")
            
            data = []
            
            try:
                import akshare as ak
            except ImportError:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="AkShare not installed"
                )
            
            if market == "us":
                try:
                    df = ak.stock_financial_us_report_em(stock=ticker, symbol="综合损益表", indicator="年报")
                    if df is not None and not df.empty:
                        for _, row in df.head(5).iterrows():
                            data.append({
                                "type": "financial",
                                "source": "AkShare",
                                "data": row.to_dict()
                            })
                except Exception as e:
                    logger.warning(f"Could not fetch US financial data for {ticker}: {e}")
            
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=data,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error fetching from AkShare: {e}")
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=[],
                success=False,
                error=str(e)
            )
