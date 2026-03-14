"""AkShare adapter for financial data."""

import sys
import os
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
        """Fetch comprehensive financial data from AkShare."""
        try:
            ticker = query.get("ticker", "")
            market = query.get("market", "cn")
            
            if not ticker:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="No ticker provided"
                )
            
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
            
            # Get income statement data
            income_df = ak.stock_financial_us_report_em(
                stock=ticker, 
                symbol="综合损益表", 
                indicator="年报"
            )
            
            if income_df is None or income_df.empty:
                return DataSourceResult(
                    source_name=self.source_name,
                    source_type=self.source_type,
                    data=[],
                    success=False,
                    error="No data returned from AkShare"
                )
            
            # Transform into standardized format
            standardized_data = self._transform_data(income_df, ticker)
            
            return DataSourceResult(
                source_name=self.source_name,
                source_type=self.source_type,
                data=standardized_data,
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
    
    def _transform_data(self, df, ticker: str) -> list[dict]:
        """Transform raw AkShare data into standardized format."""
        
        # Key metrics we want
        KEY_METRICS = [
            "主营收入",        # 营业收入
            "净利润",         # 净利润
            "毛利",          # 毛利润
            "营业利润",       # 营业利润
            "持续经营税前利润", # 税前利润
            "所得税",         # 所得税费用
            "基本每股收益-普通股",  # EPS
        ]
        
        result = []
        
        # Get unique years
        years = df['REPORT_DATE'].astype(str).str[:4].unique()
        years = sorted([y for y in years if y.isdigit()], reverse=True)[:5]  # Latest 5 years
        
        for year in years:
            year_data = df[df['REPORT_DATE'].astype(str).str.startswith(year)]
            
            if year_data.empty:
                continue
            
            # Extract key metrics for this year
            year_metrics = {}
            for _, row in year_data.iterrows():
                item_name = row.get('ITEM_NAME', '')
                amount = row.get('AMOUNT', 0)
                if item_name in KEY_METRICS:
                    year_metrics[item_name] = amount
            
            if year_metrics:
                result.append({
                    "type": "financial",
                    "source": "AkShare",
                    "year": int(year),
                    "ticker": ticker,
                    "metrics": year_metrics,
                    "report_type": "年报",
                    "data_source": "AkShare stock_financial_us_report_em"
                })
        
        return result