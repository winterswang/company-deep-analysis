"""
搜索引擎
整合 AkShare、雪球、Tavily、Exa 等数据源
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import Evidence, CredibilityLevel, EvidenceDirection, DataSource, SearchTarget


@dataclass
class SearchResult:
    """搜索结果"""
    title: str
    url: str
    content: str
    source_type: str
    credibility: CredibilityLevel


class SearchProvider(ABC):
    """搜索提供商基类"""
    
    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        """执行搜索"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass


class TavilySearchProvider(SearchProvider):
    """Tavily搜索提供商"""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            # 尝试从多个位置加载
            api_key = os.environ.get("TAVILY_API_KEY", "")
            if not api_key:
                # 尝试从.env文件加载
                env_paths = [
                    Path("/root/.openclaw/workspace/deer-flow-analysis/.env"),
                    Path(__file__).parent.parent.parent / ".env",
                ]
                for env_path in env_paths:
                    if env_path.exists():
                        with open(env_path) as f:
                            for line in f:
                                if "TAVILY_API_KEY" in line and "=" in line:
                                    api_key = line.strip().split("=", 1)[1]
                                    break
                    if api_key:
                        break
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if not self.is_available():
            return []
        
        # 限制查询长度，避免400错误
        if len(query) > 300:
            query = query[:300] + "..."
        
        # 清理查询字符串
        query = query.replace('\n', ' ').strip()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "max_results": max_results,
            "include_raw_content": False,
        }
        
        # 添加重试机制
        for attempt in range(3):
            try:
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("results", []):
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        content=item.get("content", ""),
                        source_type="tavily",
                        credibility=CredibilityLevel.P2_PROFESSIONAL
                    ))
                return results
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400:
                    # 400错误，返回空结果而不是抛出异常
                    print(f"Tavily search error (400): query too long or invalid")
                    return []
                if attempt == 2:
                    print(f"Tavily search error: {e}")
                    return []
            except Exception as e:
                if attempt == 2:
                    print(f"Tavily search error: {e}")
                    return []
        
        return []


class ExaSearchProvider(SearchProvider):
    """Exa搜索提供商"""
    
    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            # 尝试从多个位置加载
            api_key = os.environ.get("EXA_API_KEY", "")
            if not api_key:
                # 尝试从.env文件加载
                env_paths = [
                    Path("/root/.openclaw/workspace/deer-flow-analysis/.env"),
                    Path(__file__).parent.parent.parent / ".env",
                ]
                for env_path in env_paths:
                    if env_path.exists():
                        with open(env_path) as f:
                            for line in f:
                                if "EXA_API_KEY" in line and "=" in line:
                                    api_key = line.strip().split("=", 1)[1]
                                    break
                    if api_key:
                        break
        self.api_key = api_key
        self.base_url = "https://api.exa.ai/search"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if not self.is_available():
            return []
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "numResults": max_results,
            "useAutoprompt": True,
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get("results", []):
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("text", "")[:1000],
                    source_type="exa",
                    credibility=CredibilityLevel.P2_PROFESSIONAL
                ))
            return results
        
        except Exception as e:
            print(f"Exa search error: {e}")
            return []


class AkShareProvider(SearchProvider):
    """AkShare数据提供商"""
    
    def __init__(self, akshare_service_path: str = ""):
        self.akshare_service_path = akshare_service_path
        self._akshare = None
    
    def is_available(self) -> bool:
        try:
            import akshare
            return True
        except ImportError:
            return False
    
    def search(self, query: str) -> List[SearchResult]:
        """AkShare搜索（主要是财务数据查询）"""
        results = []
        
        try:
            import akshare as ak
            
            # 尝试获取股票基本信息
            if "财务" in query or "利润" in query or "ROIC" in query:
                # 这里需要根据具体查询解析股票代码
                # 简化处理，返回提示信息
                results.append(SearchResult(
                    title="AkShare财务数据",
                    url="akshare://financial",
                    content=f"可通过AkShare获取财务数据。查询: {query}",
                    source_type="akshare",
                    credibility=CredibilityLevel.P0_OFFICIAL
                ))
        
        except Exception as e:
            print(f"AkShare error: {e}")
        
        return results
    
    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        try:
            import akshare as ak
            
            # 判断是否为A股
            if symbol.isdigit() or symbol.startswith(("sh", "sz")):
                return self._get_a_stock_data(symbol)
            else:
                # 美股
                return self._get_us_stock_data(symbol)
        
        except Exception as e:
            print(f"Get financial data error: {e}")
            return {}
    
    def _get_a_stock_data(self, symbol: str) -> Dict[str, Any]:
        """获取A股数据"""
        try:
            import akshare as ak
            
            # 标准化代码
            if symbol.isdigit():
                if symbol.startswith("6"):
                    symbol = f"sh{symbol}"
                else:
                    symbol = f"sz{symbol}"
            
            data = {}
            
            # 获取财务指标
            try:
                df = ak.stock_financial_analysis_indicator(symbol=symbol)
                if df is not None and not df.empty:
                    data["financial_indicators"] = df.to_dict("records")[-5:]  # 最近5期
            except:
                pass
            
            return data
        
        except Exception as e:
            print(f"Get A stock data error: {e}")
            return {}
    
    def _get_us_stock_data(self, symbol: str) -> Dict[str, Any]:
        """获取美股数据"""
        try:
            import akshare as ak
            
            data = {}
            
            # 获取美股财务数据
            try:
                df = ak.stock_us_fundamental(symbol=symbol)
                if df is not None and not df.empty:
                    data["fundamental"] = df.to_dict("records")[-5:]
            except:
                pass
            
            return data
        
        except Exception as e:
            print(f"Get US stock data error: {e}")
            return {}


class XueqiuProvider(SearchProvider):
    """雪球数据提供商"""
    
    def __init__(self):
        self.base_url = "https://xueqiu.com"
        self.cookies = None
    
    def is_available(self) -> bool:
        # 雪球需要登录，这里简化处理
        return True
    
    def search(self, query: str) -> List[SearchResult]:
        """雪球搜索"""
        # 雪球搜索需要通过爬虫实现
        # 这里返回提示信息
        results = []
        results.append(SearchResult(
            title="雪球分析",
            url="xueqiu://search",
            content=f"可通过雪球分析获取中文投资者观点。查询: {query}",
            source_type="xueqiu",
            credibility=CredibilityLevel.P3_GENERAL
        ))
        return results


class SearchEngine:
    """搜索引擎主类"""
    
    def __init__(self):
        self.providers = {
            DataSource.TAVILY: TavilySearchProvider(),
            DataSource.EXA: ExaSearchProvider(),
            DataSource.AKSHARE: AkShareProvider(),
            DataSource.XUEQIU: XueqiuProvider(),
        }
    
    def search(self, target: SearchTarget) -> List[Evidence]:
        """执行搜索"""
        provider = self.providers.get(target.data_source)
        if not provider or not provider.is_available():
            print(f"Provider {target.data_source} not available")
            return []
        
        results = provider.search(target.query)
        
        evidences = []
        for i, result in enumerate(results):
            evidence = Evidence(
                id=f"E{target.id}_{i}",
                source=result.url,
                source_type=result.source_type,
                credibility=result.credibility,
                content=result.content,
                relevance=self._assess_relevance(result.content, target),
                direction=EvidenceDirection.NEUTRAL,  # 需要后续评估
                doubt_id=target.doubt_id,
            )
            evidences.append(evidence)
        
        return evidences
    
    def search_multi_source(self, query: str, sources: List[DataSource]) -> List[Evidence]:
        """多源搜索"""
        all_evidences = []
        
        for source in sources:
            provider = self.providers.get(source)
            if provider and provider.is_available():
                results = provider.search(query)
                for i, result in enumerate(results):
                    evidence = Evidence(
                        id=f"E{source.value}_{i}",
                        source=result.url,
                        source_type=result.source_type,
                        credibility=result.credibility,
                        content=result.content,
                        relevance=0.5,  # 默认相关性
                        direction=EvidenceDirection.NEUTRAL,
                    )
                    all_evidences.append(evidence)
        
        return all_evidences
    
    def _assess_relevance(self, content: str, target: SearchTarget) -> float:
        """评估相关性"""
        # 简化的相关性评估
        # 实际应该用LLM评估
        keywords = target.query.lower().split()
        content_lower = content.lower()
        
        matches = sum(1 for kw in keywords if kw in content_lower)
        return min(1.0, matches / max(1, len(keywords)))
    
    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        akshare_provider = self.providers.get(DataSource.AKSHARE)
        if akshare_provider and akshare_provider.is_available():
            return akshare_provider.get_financial_data(symbol)
        return {}