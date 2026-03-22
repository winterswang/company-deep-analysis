"""
Company Deep Analysis - Data Collector Module

提供标准化数据查询能力，作为工具箱被其他模块调用
"""

from .tools import DataQueryTools
from .schemas import DataResponse, FinancialData, CashflowData, XueqiuData, SearchData, LocalData

__version__ = "1.0.0"
__all__ = [
    "DataQueryTools",
    "DataResponse",
    "FinancialData", 
    "CashflowData",
    "XueqiuData",
    "SearchResult",
    "LocalResult"
]