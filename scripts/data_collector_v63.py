"""
V6.3 数据源集成

实际集成：
1. AkShare (P0) - 财务数据
2. 雪球爬虫 (P0) - 专业分析
3. 本地数据 (P0) - link collection
4. Tavily (P2) - 搜索引擎
5. Exa (P2) - 深度搜索
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.data_sources_v62 import DataSourceType, get_data_quality, DATA_SOURCES
from core.analyzer_v62 import DataPoint


class AkShareProvider:
    """AkShare数据提供者 (P0)"""
    
    def __init__(self):
        self.quality = "P0"
    
    def fetch_financial_data(self, ticker: str, market: str = "us") -> List[DataPoint]:
        """获取财务数据"""
        print(f"\n[AkShare P0] 获取 {ticker} 财务数据...")
        data_points = []
        
        try:
            import akshare as ak
            
            if market == "us":
                # 美股数据
                try:
                    # 获取美股实时行情
                    df = ak.stock_zh_a_spot_em()  # A股数据作为示例
                    # 实际应该使用美股API
                    
                except Exception as e:
                    print(f"  ⚠️ AkShare美股数据获取失败: {e}")
                    
            elif market == "cn":
                # A股数据
                try:
                    # 获取个股财务数据
                    df = ak.stock_financial_analysis_indicator(symbol=ticker)
                    if df is not None and not df.empty:
                        latest = df.iloc[0]
                        data_points.append(DataPoint(
                            name="财务指标",
                            value=str(latest.to_dict()),
                            source="AkShare",
                            quality="P0",
                            timestamp=datetime.now().isoformat(),
                            validity="最新",
                            notes="A股财务数据"
                        ))
                        print(f"  ✅ 获取财务数据成功")
                except Exception as e:
                    print(f"  ⚠️ AkShare A股数据获取失败: {e}")
                    
        except ImportError:
            print("  ⚠️ AkShare未安装，请运行: pip install akshare")
        except Exception as e:
            print(f"  ⚠️ AkShare错误: {e}")
        
        return data_points
    
    def search_company(self, company_name: str) -> List[DataPoint]:
        """搜索公司"""
        print(f"\n[AkShare P0] 搜索 {company_name}...")
        
        # AkShare不直接支持搜索，返回空
        print("  ⚠️ AkShare不支持公司搜索")
        return []


class XueqiuProvider:
    """雪球数据提供者 (P0)"""
    
    def __init__(self):
        self.quality = "P0"
        self.report_dir = Path("/root/.openclaw/workspace/xueqiu-analyzer-skill/data/reports")
        self.crawler_dir = Path("/root/.openclaw/workspace/xueqiu-crawler/data")
    
    def fetch_analysis_reports(self, company: str) -> List[DataPoint]:
        """获取分析报告"""
        print(f"\n[雪球 P0] 搜索 {company} 分析报告...")
        data_points = []
        
        try:
            # 检查雪球分析报告
            if self.report_dir.exists():
                reports = list(self.report_dir.glob(f"*{company}*.md"))
                if reports:
                    latest = max(reports, key=lambda x: x.stat().st_mtime)
                    content = self._read_report(latest)
                    data_points.append(DataPoint(
                        name="雪球分析报告",
                        value=latest.name,
                        source="雪球爬虫",
                        quality="P0",
                        timestamp=datetime.now().isoformat(),
                        validity=datetime.fromtimestamp(latest.stat().st_mtime).strftime('%Y-%m-%d'),
                        notes=f"报告路径: {latest}\n内容摘要: {content[:500]}..."
                    ))
                    print(f"  ✅ 找到分析报告: {latest.name}")
                else:
                    print(f"  ⚠️ 未找到 {company} 的雪球分析报告")
            
            # 检查爬虫数据
            if self.crawler_dir.exists():
                crawled = self._search_crawled_data(company)
                if crawled:
                    data_points.extend(crawled)
                    
        except Exception as e:
            print(f"  ⚠️ 雪球数据获取失败: {e}")
        
        return data_points
    
    def _read_report(self, file_path: Path) -> str:
        """读取报告内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""
    
    def _search_crawled_data(self, company: str) -> List[DataPoint]:
        """搜索爬取的数据"""
        data_points = []
        
        # 遍历用户目录
        for user_dir in self.crawler_dir.iterdir():
            if user_dir.is_dir():
                for md_file in user_dir.glob("*.md"):
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 搜索公司名
                            if company.lower() in content.lower():
                                data_points.append(DataPoint(
                                    name="雪球文章",
                                    value=md_file.name,
                                    source="雪球爬虫",
                                    quality="P0",
                                    timestamp=datetime.now().isoformat(),
                                    validity=md_file.stem,
                                    notes=f"路径: {md_file}"
                                ))
                    except:
                        pass
        
        if data_points:
            print(f"  ✅ 找到 {len(data_points)} 篇相关文章")
        return data_points[:5]  # 最多返回5篇


class LocalDataProvider:
    """本地数据提供者 (P0)"""
    
    def __init__(self):
        self.quality = "P0"
        self.inbox_dir = Path("/root/.openclaw/workspace/ideas-and-notes/inbox")
        self.memory_dir = Path("/root/.openclaw/workspace/memory")
    
    def search_local_data(self, company: str) -> List[DataPoint]:
        """搜索本地收藏数据"""
        print(f"\n[本地数据 P0] 搜索 {company} 收藏...")
        data_points = []
        
        try:
            # 搜索inbox目录
            if self.inbox_dir.exists():
                for date_dir in sorted(self.inbox_dir.iterdir(), reverse=True)[:30]:  # 最近30天
                    if date_dir.is_dir():
                        for md_file in date_dir.glob("*.md"):
                            if company.lower() in md_file.name.lower():
                                content = self._read_file(md_file)
                                data_points.append(DataPoint(
                                    name="本地收藏",
                                    value=md_file.name,
                                    source="本地数据",
                                    quality="P0",
                                    timestamp=datetime.now().isoformat(),
                                    validity=date_dir.name,
                                    notes=f"路径: {md_file}\n摘要: {content[:200]}..."
                                ))
            
            if data_points:
                print(f"  ✅ 找到 {len(data_points)} 个本地收藏")
            else:
                print(f"  ⚠️ 未找到 {company} 相关的本地收藏")
                
        except Exception as e:
            print(f"  ⚠️ 本地数据搜索失败: {e}")
        
        return data_points[:5]
    
    def _read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return ""


class TavilyProvider:
    """Tavily搜索提供者 (P2)"""
    
    def __init__(self):
        self.quality = "P2"
        self.api_key = self._load_api_key()
    
    def _load_api_key(self) -> str:
        """加载API Key"""
        key = os.environ.get("TAVILY_API_KEY", "")
        if not key:
            env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("TAVILY_API_KEY="):
                            key = line.strip().split("=", 1)[1]
                            break
        return key
    
    def search(self, query: str, max_results: int = 5) -> List[DataPoint]:
        """执行搜索"""
        print(f"\n[Tavily P2] 搜索: {query}...")
        data_points = []
        
        if not self.api_key:
            print("  ⚠️ Tavily API未配置")
            return data_points
        
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": "advanced"
            }
            
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                for item in result.get("results", []):
                    data_points.append(DataPoint(
                        name=item.get("title", ""),
                        value=item.get("content", "")[:500],
                        source="Tavily",
                        quality="P2",
                        timestamp=datetime.now().isoformat(),
                        validity="实时",
                        notes=f"URL: {item.get('url', '')}"
                    ))
                print(f"  ✅ 获取 {len(data_points)} 条搜索结果")
            else:
                print(f"  ⚠️ Tavily搜索失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️ Tavily搜索错误: {e}")
        
        return data_points


class ExaProvider:
    """Exa搜索提供者 (P2)"""
    
    def __init__(self):
        self.quality = "P2"
        self.api_key = self._load_api_key()
    
    def _load_api_key(self) -> str:
        """加载API Key"""
        key = os.environ.get("EXA_API_KEY", "")
        if not key:
            env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith("EXA_API_KEY="):
                            key = line.strip().split("=", 1)[1]
                            break
        return key
    
    def search(self, query: str, max_results: int = 5) -> List[DataPoint]:
        """执行搜索"""
        print(f"\n[Exa P2] 深度搜索: {query}...")
        data_points = []
        
        if not self.api_key:
            print("  ⚠️ Exa API未配置")
            return data_points
        
        try:
            url = "https://api.exa.ai/search"
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "query": query,
                "numResults": max_results,
                "useAutoprompt": True
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                for item in result.get("results", []):
                    data_points.append(DataPoint(
                        name=item.get("title", ""),
                        value=item.get("text", "")[:500],
                        source="Exa",
                        quality="P2",
                        timestamp=datetime.now().isoformat(),
                        validity="实时",
                        notes=f"URL: {item.get('url', '')}"
                    ))
                print(f"  ✅ 获取 {len(data_points)} 条深度搜索结果")
            else:
                print(f"  ⚠️ Exa搜索失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ⚠️ Exa搜索错误: {e}")
        
        return data_points


class IntegratedDataCollector:
    """集成数据收集器"""
    
    def __init__(self):
        self.akshare = AkShareProvider()
        self.xueqiu = XueqiuProvider()
        self.local = LocalDataProvider()
        self.tavily = TavilyProvider()
        self.exa = ExaProvider()
        
        self.all_data: List[DataPoint] = []
    
    def collect_all(self, company: str, ticker: str = None, market: str = "us") -> List[DataPoint]:
        """收集所有数据"""
        print("=" * 60)
        print(f"【V6.3 数据收集】{company}")
        print("=" * 60)
        
        # 1. AkShare财务数据 (P0)
        if ticker:
            ak_data = self.akshare.fetch_financial_data(ticker, market)
            self.all_data.extend(ak_data)
        
        # 2. 雪球分析报告 (P0)
        xq_data = self.xueqiu.fetch_analysis_reports(company)
        self.all_data.extend(xq_data)
        
        # 3. 本地收藏数据 (P0)
        local_data = self.local.search_local_data(company)
        self.all_data.extend(local_data)
        
        # 4. Tavily搜索 (P2)
        tavily_data = self.tavily.search(f"{company} financial analysis investment")
        self.all_data.extend(tavily_data)
        
        # 5. Exa深度搜索 (P2)
        exa_data = self.exa.search(f"{company} company analysis valuation")
        self.all_data.extend(exa_data)
        
        return self.all_data
    
    def get_summary(self) -> Dict[str, Any]:
        """获取数据收集摘要"""
        valid = [d for d in self.all_data if d.is_valid()]
        invalid = [d for d in self.all_data if not d.is_valid()]
        
        by_source = {}
        for d in self.all_data:
            if d.source not in by_source:
                by_source[d.source] = []
            by_source[d.source].append(d)
        
        return {
            "total": len(self.all_data),
            "valid": len(valid),
            "invalid": len(invalid),
            "by_source": {k: len(v) for k, v in by_source.items()},
            "valid_data": valid
        }


def main():
    """测试数据收集"""
    collector = IntegratedDataCollector()
    
    # 测试任天堂数据收集
    data = collector.collect_all("Nintendo", "NTDOY", "us")
    
    summary = collector.get_summary()
    print("\n" + "=" * 60)
    print("数据收集摘要:")
    print("=" * 60)
    print(f"总数据: {summary['total']} 条")
    print(f"有效数据 (P2及以上): {summary['valid']} 条")
    print(f"低质量数据 (P3及以下): {summary['invalid']} 条")
    print("\n按来源分类:")
    for source, count in summary['by_source'].items():
        print(f"  {source}: {count} 条")


if __name__ == "__main__":
    main()