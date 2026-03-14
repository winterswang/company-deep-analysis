"""
V6.3.2 数据收集器 - 集成本地数据

从多个来源收集数据：
1. 雪球爬虫 (P0)
2. AkShare (P0)
3. 本地文件 (P0) - PDF/Excel/文本
4. Tavily (P2)
5. Exa (P2)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

sys.path.insert(0, str(Path(__file__).parent))

from config.data_sources_v62 import DataSourceType, get_data_quality
from core.analyzer_v62 import DataPoint
from xueqiu_quality_evaluator import XueqiuDataQualityEvaluator


class XueqiuStockPageCrawler:
    """雪球股票详情页爬虫 (P0)"""
    
    def __init__(self):
        self.quality = "P0"
        self.crawler_path = Path("/root/.openclaw/workspace/xueqiu-analyzer-skill/scripts/stock_crawler_v2.py")
        self.smart_crawler_path = Path("/root/.openclaw/workspace/xueqiu-analyzer-skill/scripts/smart_crawler_v2.py")
        self.quality_evaluator = XueqiuDataQualityEvaluator()
    
    def crawl_stock_page(self, symbol: str, max_discussions: int = 20, max_news: int = 15) -> List[DataPoint]:
        """爬取股票详情页"""
        print(f"\n[雪球 P0] 爬取 {symbol} 股票详情页...")
        data_points = []
        
        try:
            # 导入雪球爬虫
            sys.path.insert(0, str(self.crawler_path.parent))
            from stock_crawler_v2 import XueqiuStockCrawlerV2
            
            # 创建爬虫实例
            crawler = XueqiuStockCrawlerV2(headless=True)
            
            # 爬取股票详情
            stock_info = crawler.crawl(symbol, max_discussions=max_discussions, max_news=max_news)
            
            if stock_info:
                # 处理讨论 - 使用质量评估器
                discussion_count = 0
                filtered_discussion_count = 0
                for d in stock_info.discussions[:20]:
                    assessment = self.quality_evaluator.evaluate_discussion(d.content)
                    if assessment.adjusted_quality in ["P0", "P1", "P2"]:
                        data_points.append(DataPoint(
                            name="雪球讨论",
                            value=d.content[:500],
                            source="雪球爬虫-讨论",
                            quality=assessment.adjusted_quality,
                            timestamp=datetime.now().isoformat(),
                            validity=d.time,
                            notes=f"作者: {d.author}, 链接: {d.link} | {assessment.reason}"
                        ))
                        discussion_count += 1
                    else:
                        filtered_discussion_count += 1
                
                # 处理资讯 - 固定P2
                news_count = 0
                filtered_news_count = 0
                for n in stock_info.news[:15]:
                    assessment = self.quality_evaluator.evaluate_news(n.title, n.content if hasattr(n, 'content') else "")
                    if assessment.adjusted_quality in ["P0", "P1", "P2"]:
                        data_points.append(DataPoint(
                            name=n.title,
                            value=n.content if hasattr(n, 'content') else n.title,
                            source="雪球爬虫-资讯",
                            quality=assessment.adjusted_quality,
                            timestamp=datetime.now().isoformat(),
                            validity=n.time,
                            notes=f"来源: {n.source}, 链接: {n.link}"
                        ))
                        news_count += 1
                    else:
                        filtered_news_count += 1
                
                # 处理公告 - 固定P1
                for n in stock_info.notices[:10]:
                    assessment = self.quality_evaluator.evaluate_notice(n.title)
                    data_points.append(DataPoint(
                        name=n.title,
                        value="",
                        source="雪球爬虫-公告",
                        quality=assessment.adjusted_quality,
                        timestamp=datetime.now().isoformat(),
                        validity="",
                        notes=f"链接: {n.link}"
                    ))
                
                # 处理文章 - 根据内容长度判断P0/P2
                article_p0_count = 0
                article_p2_count = 0
                for a in stock_info.articles[:10]:
                    assessment = self.quality_evaluator.evaluate_article(a.title, a.content)
                    data_points.append(DataPoint(
                        name=a.title,
                        value=a.content[:500] if len(a.content) > 500 else a.content,
                        source="雪球爬虫-专栏",
                        quality=assessment.adjusted_quality,
                        timestamp=datetime.now().isoformat(),
                        validity=a.time,
                        notes=f"作者: {a.author}, 链接: {a.link} | {assessment.reason}"
                    ))
                    if assessment.adjusted_quality == "P0":
                        article_p0_count += 1
                    else:
                        article_p2_count += 1
                
                # 财务数据
                if stock_info.financial_data:
                    for key, value in stock_info.financial_data.items():
                        data_points.append(DataPoint(
                            name=key,
                            value=str(value),
                            source="雪球爬虫-财务",
                            quality="P0",
                            timestamp=datetime.now().isoformat(),
                            validity="实时",
                            notes="雪球财务数据"
                        ))
                
                print(f"  ✅ 爬取成功:")
                print(f"     讨论: {discussion_count}条有效 (过滤{filtered_discussion_count}条低质量)")
                print(f"     资讯: {news_count}条有效 (过滤{filtered_news_count}条低质量)")
                print(f"     公告: {len(stock_info.notices[:10])}条 (P1)")
                print(f"     专栏: {article_p0_count}条P0 + {article_p2_count}条P2")
            
        except ImportError as e:
            print(f"  ⚠️ 雪球爬虫导入失败: {e}")
            print(f"  尝试使用 smart_crawler_v2...")
            
            # 尝试使用 smart_crawler_v2
            try:
                from smart_crawler_v2 import XueqiuSmartCrawlerV2
                crawler = XueqiuSmartCrawlerV2()
                result = crawler.crawl(symbol, max_rounds=1)
                
                if result:
                    # 处理结果
                    for article in result.get("articles", [])[:10]:
                        data_points.append(DataPoint(
                            name="雪球文章",
                            value=article.get("title", ""),
                            source="雪球爬虫-智能",
                            quality="P0",
                            timestamp=datetime.now().isoformat(),
                            validity="",
                            notes=f"内容: {article.get('content', '')[:300]}..."
                        ))
                    print(f"  ✅ 使用智能爬虫成功: {len(result.get('articles', []))} 文章")
                    
            except Exception as e2:
                print(f"  ⚠️ 智能爬虫也失败: {e2}")
                
        except Exception as e:
            print(f"  ⚠️ 雪球爬取失败: {e}")
            import traceback
            traceback.print_exc()
        
        return data_points
    
    def search_by_company_name(self, company: str) -> List[DataPoint]:
        """通过公司名搜索（需要先找到股票代码）"""
        print(f"\n[雪球 P0] 搜索 {company} 股票代码...")
        
        # 公司名到股票代码的映射
        company_symbol_map = {
            "nintendo": "NTDOY",
            "任天堂": "NTDOY",
            "fiserv": "FISV",
            "apple": "AAPL",
            "苹果": "AAPL",
            "microsoft": "MSFT",
            "微软": "MSFT",
            "google": "GOOGL",
            "谷歌": "GOOGL",
            "amazon": "AMZN",
            "亚马逊": "AMZN",
            "tencent": "0700.HK",
            "腾讯": "0700.HK",
            "alibaba": "BABA",
            "阿里巴巴": "BABA",
        }
        
        # 查找股票代码
        symbol = company_symbol_map.get(company.lower())
        
        if symbol:
            print(f"  找到股票代码: {symbol}")
            return self.crawl_stock_page(symbol)
        else:
            print(f"  ⚠️ 未找到 {company} 的股票代码，尝试用公司名爬取...")
            # 尝试直接使用公司名作为 symbol
            return self.crawl_stock_page(company.upper())


class AkShareFinancialProvider:
    """AkShare财务数据提供者 (P0)"""
    
    def __init__(self):
        self.quality = "P0"
    
    def get_financial_data(self, ticker: str, market: str = "us") -> List[DataPoint]:
        """获取财务数据"""
        print(f"\n[AkShare P0] 获取 {ticker} 财务数据...")
        data_points = []
        
        try:
            import akshare as ak
            
            if market == "us":
                # 美股数据
                try:
                    # 获取美股行情
                    df = ak.stock_us_spot_em()
                    stock_data = df[df['代码'] == ticker]
                    
                    if not stock_data.empty:
                        row = stock_data.iloc[0]
                        data_points.extend([
                            DataPoint("股价", str(row.get('最新价', '')), "AkShare", "P0", datetime.now().isoformat(), "实时"),
                            DataPoint("涨跌幅", str(row.get('涨跌幅', '')), "AkShare", "P0", datetime.now().isoformat(), "实时"),
                        ])
                        print(f"  ✅ 获取美股行情成功")
                        
                except Exception as e:
                    print(f"  ⚠️ 美股行情获取失败: {e}")
                
                # 尝试获取财务指标（东方财富美股数据）
                try:
                    df_financial = ak.stock_financial_us_analysis_indicator_em(symbol=ticker, indicator='年报')
                    if df_financial is not None and not df_financial.empty:
                        latest = df_financial.iloc[0]
                        
                        # 提取关键财务指标
                        metrics = [
                            ("ROE", latest.get('ROE_AVG')),
                            ("ROA", latest.get('ROA')),
                            ("毛利率", latest.get('GROSS_PROFIT_RATIO')),
                            ("净利率", latest.get('NET_PROFIT_RATIO')),
                            ("营收", latest.get('OPERATE_INCOME')),
                            ("净利润", latest.get('PARENT_HOLDER_NETPROFIT')),
                            ("EPS", latest.get('BASIC_EPS')),
                            ("资产负债率", latest.get('DEBT_ASSET_RATIO')),
                            ("流动比率", latest.get('CURRENT_RATIO')),
                        ]
                        
                        for name, value in metrics:
                            if value is not None and not (isinstance(value, float) and value != value):
                                data_points.append(DataPoint(
                                    name=name,
                                    value=str(value),
                                    source="AkShare-东方财富",
                                    quality="P0",
                                    timestamp=datetime.now().isoformat(),
                                    validity="年报"
                                ))
                        print(f"  ✅ 获取美股财务指标成功: {len(metrics)} 个指标")
                        
                except Exception as e:
                    print(f"  ⚠️ 财务指标获取失败: {e}")
                    
            elif market == "cn":
                # A股数据
                try:
                    df = ak.stock_financial_analysis_indicator(symbol=ticker)
                    if df is not None and not df.empty:
                        for _, row in df.head(10).iterrows():
                            data_points.append(DataPoint(
                                name=str(row.get('指标', '')),
                                value=str(row.get('值', '')),
                                source="AkShare",
                                quality="P0",
                                timestamp=datetime.now().isoformat(),
                                validity="最新"
                            ))
                        print(f"  ✅ 获取A股财务数据成功")
                        
                except Exception as e:
                    print(f"  ⚠️ A股数据获取失败: {e}")
                    
        except ImportError:
            print("  ⚠️ AkShare未安装，请运行: pip install akshare")
        except Exception as e:
            print(f"  ⚠️ AkShare错误: {e}")
        
        return data_points


class IntegratedDataCollectorV63:
    """V6.3.2 完整数据收集器 - 支持本地文件"""
    
    def __init__(self, local_data_dir: str = None):
        self.xueqiu = XueqiuStockPageCrawler()
        self.akshare = AkShareFinancialProvider()
        # 保留 Tavily 和 Exa
        self.tavily_key = self._load_api_key("TAVILY_API_KEY")
        self.exa_key = self._load_api_key("EXA_API_KEY")
        
        # 本地数据加载器
        self.local_data_dir = local_data_dir or str(Path(__file__).parent.parent / "data" / "local")
        
        self.all_data: List[DataPoint] = []
    
    def _load_api_key(self, key_name: str) -> str:
        """加载API Key"""
        key = os.environ.get(key_name, "")
        if not key:
            env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith(f"{key_name}="):
                            key = line.strip().split("=", 1)[1]
                            break
        return key
    
    def collect_all(self, company: str, ticker: str = None, market: str = "us") -> List[DataPoint]:
        """收集所有数据（包含本地文件）"""
        print("=" * 60)
        print(f"【V6.3.2 完整数据收集】{company}")
        print("=" * 60)
        
        # 0. 本地数据 (P0) - 最高优先级
        print("\n[本地数据 P0] 加载本地文件...")
        try:
            from local_data_loader import LocalDataLoader
            loader = LocalDataLoader(self.local_data_dir)
            local_data = loader.load_all(company)
            if local_data:
                self.all_data.extend(local_data)
                print(f"  ✅ 加载 {len(local_data)} 条本地数据")
            else:
                print("  ⚠️ 未找到本地数据文件")
        except Exception as e:
            print(f"  ⚠️ 本地数据加载失败: {e}")
        
        # 1. 雪球爬虫 (P0) - 优先级最高
        xq_data = self.xueqiu.search_by_company_name(company)
        if not xq_data and ticker:
            xq_data = self.xueqiu.crawl_stock_page(ticker)
        self.all_data.extend(xq_data)
        
        # 2. AkShare财务数据 (P0)
        if ticker:
            ak_data = self.akshare.get_financial_data(ticker, market)
            self.all_data.extend(ak_data)
        
        # 3. Tavily搜索 (P2) - 补充
        if self.tavily_key:
            tavily_data = self._tavily_search(f"{company} financial analysis investment")
            self.all_data.extend(tavily_data)
        
        # 4. Exa深度搜索 (P2) - 补充
        if self.exa_key:
            exa_data = self._exa_search(f"{company} company analysis valuation")
            self.all_data.extend(exa_data)
        
        return self.all_data
    
    def _tavily_search(self, query: str) -> List[DataPoint]:
        """Tavily搜索"""
        import requests
        
        print(f"\n[Tavily P2] 搜索: {query}...")
        data_points = []
        
        try:
            url = "https://api.tavily.com/search"
            payload = {
                "api_key": self.tavily_key,
                "query": query,
                "max_results": 5
            }
            
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                for item in result.get("results", []):
                    data_points.append(DataPoint(
                        name=item.get("title", ""),
                        value=item.get("content", "")[:300],
                        source="Tavily",
                        quality="P2",
                        timestamp=datetime.now().isoformat(),
                        validity="实时",
                        notes=f"URL: {item.get('url', '')}"
                    ))
                print(f"  ✅ 获取 {len(data_points)} 条搜索结果")
        except Exception as e:
            print(f"  ⚠️ Tavily搜索失败: {e}")
        
        return data_points
    
    def _exa_search(self, query: str) -> List[DataPoint]:
        """Exa搜索"""
        import requests
        
        print(f"\n[Exa P2] 搜索: {query}...")
        data_points = []
        
        try:
            url = "https://api.exa.ai/search"
            headers = {"x-api-key": self.exa_key, "Content-Type": "application/json"}
            payload = {"query": query, "numResults": 5}
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                for item in result.get("results", []):
                    data_points.append(DataPoint(
                        name=item.get("title", ""),
                        value=item.get("text", "")[:300],
                        source="Exa",
                        quality="P2",
                        timestamp=datetime.now().isoformat(),
                        validity="实时",
                        notes=f"URL: {item.get('url', '')}"
                    ))
                print(f"  ✅ 获取 {len(data_points)} 条搜索结果")
        except Exception as e:
            print(f"  ⚠️ Exa搜索失败: {e}")
        
        return data_points
    
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


if __name__ == "__main__":
    collector = IntegratedDataCollectorV63()
    data = collector.collect_all("Nintendo", "NTDOY", "us")
    
    summary = collector.get_summary()
    print("\n" + "=" * 60)
    print("数据收集摘要:")
    print("=" * 60)
    print(f"总数据: {summary['total']} 条")
    print(f"有效数据 (P2及以上): {summary['valid']} 条")
    print("\n按来源分类:")
    for source, count in summary['by_source'].items():
        print(f"  {source}: {count} 条")