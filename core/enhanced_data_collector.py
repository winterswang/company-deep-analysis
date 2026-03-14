"""
V7.0 增强版数据收集器

核心改进：
1. 使用正确的 AkShare API 调用方式（参考 akshare_docs 项目）
2. 多次尝试，循环搜索，不轻易放弃
3. 收集 5 年趋势数据 + TTM 数据
4. 全面收集所有关键财务指标
"""

import sys
import time
import requests
import akshare as ak
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


class EnhancedDataCollector:
    """增强版数据收集器 - 持续努力获取数据"""
    
    def __init__(self):
        self.tavily_key = self._load_api_key("TAVILY_API_KEY")
        self.exa_key = self._load_api_key("EXA_API_KEY")
        self.collected_data = {}
        self.search_history = []
        
        # 添加 akshare_docs 路径
        akshare_docs_path = Path("/root/.openclaw/workspace/akshare_docs")
        if akshare_docs_path.exists():
            sys.path.insert(0, str(akshare_docs_path))
    
    def _load_api_key(self, key_name: str) -> Optional[str]:
        """加载 API Key"""
        import os
        key = os.environ.get(key_name)
        if not key:
            env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith(f"{key_name}="):
                            return line.strip().split("=", 1)[1]
        return key
    
    def collect_all_financial_data(
        self, 
        company: str, 
        ticker: str, 
        market: str = "us"
    ) -> Dict[str, Any]:
        """
        全面收集财务数据 - 使用正确的 AkShare API
        
        目标数据：
        1. ROIC/ROE - 5年趋势 + TTM
        2. 毛利率 - 5年趋势 + TTM
        3. 营收增速 - 5年趋势
        4. 净利润增速 - 5年趋势
        5. 现金流 - 5年趋势
        6. 费用率 - 5年趋势
        7. 周转率指标
        8. 资产负债表关键项
        """
        
        print("=" * 70)
        print("V7.0 增强版数据收集（正确 AkShare API）")
        print("持续努力获取 5 年趋势数据 + TTM")
        print("=" * 70)
        
        all_data = {}
        
        if market == "us":
            # 美股：使用正确的 AkShare API
            all_data = self._collect_us_financial_data(ticker)
        elif market == "cn":
            # A股：使用东方财富 API
            all_data = self._collect_cn_financial_data(ticker)
        
        # 补充搜索数据
        if len(all_data) < 10:
            print("\n补充搜索数据...")
            search_data = self._collect_from_search(company, ticker)
            all_data.update(search_data)
        
        # 补充雪球数据（需求文档要求）
        xueqiu_data = self._collect_xueqiu_data(company, ticker)
        if xueqiu_data:
            print(f"\n雪球数据补充: {len(xueqiu_data)} 条")
            all_data.update(xueqiu_data)
        
        print("\n" + "=" * 70)
        print(f"数据收集完成: {len(all_data)} 个指标")
        print("=" * 70)
        
        return all_data
    
    def _collect_us_financial_data(self, ticker: str) -> Dict[str, Any]:
        """
        收集美股财务数据 - 使用正确的 AkShare API
        """
        
        all_data = {}
        
        print("\n【美股财务数据 - AkShare API】")
        
        # 1. ROIC 计算（5年趋势）
        print("\n1. ROIC 计算:")
        try:
            from akshare_service.skills.finance import calculate_roic_us
            df_roic = calculate_roic_us(ticker, years=5)
            if df_roic is not None and not df_roic.empty:
                roic_data = {}
                for _, row in df_roic.iterrows():
                    roic_data[int(row['year'])] = round(row['roic'], 2)
                all_data['ROIC'] = roic_data
                print(f"   ✅ ROIC: {roic_data}")
                
                # 同时获取相关数据
                all_data['NOPAT'] = dict(zip(df_roic['year'], df_roic['nopat']))
                all_data['投入资本'] = dict(zip(df_roic['year'], df_roic['invested_capital']))
                all_data['净利润'] = dict(zip(df_roic['year'], df_roic['net_profit']))
                all_data['营收'] = dict(zip(df_roic['year'], df_roic['revenue']))
        except Exception as e:
            print(f"   ⚠️ ROIC 计算失败: {e}")
        
        # 2. 利润表数据
        print("\n2. 利润表数据:")
        try:
            df_profit = ak.stock_financial_us_report_em(stock=ticker, symbol='综合损益表', indicator='年报')
            if df_profit is not None and not df_profit.empty:
                # 透视转换
                profit_pivot = df_profit.pivot(index='REPORT_DATE', columns='ITEM_NAME', values='AMOUNT').reset_index()
                profit_pivot['REPORT_DATE'] = pd.to_datetime(profit_pivot['REPORT_DATE'])
                
                # 提取关键指标
                for _, row in profit_pivot.iterrows():
                    year = row['REPORT_DATE'].year
                    # 毛利率
                    revenue = row.get('Total revenue') or row.get('营业收入') or 0
                    cost = row.get('Cost of revenue') or row.get('营业成本') or 0
                    if revenue > 0:
                        gross_margin = (revenue - cost) / revenue * 100
                        if '毛利率' not in all_data:
                            all_data['毛利率'] = {}
                        all_data['毛利率'][year] = round(gross_margin, 2)
                    
                    # 净利率
                    net_income = row.get('Net income') or row.get('净利润') or 0
                    if revenue > 0:
                        net_margin = net_income / revenue * 100
                        if '净利率' not in all_data:
                            all_data['净利率'] = {}
                        all_data['净利率'][year] = round(net_margin, 2)
                
                print(f"   ✅ 利润表: {len(profit_pivot)} 年数据")
        except Exception as e:
            print(f"   ⚠️ 利润表获取失败: {e}")
        
        # 3. 资产负债表数据
        print("\n3. 资产负债表数据:")
        try:
            df_balance = ak.stock_financial_us_report_em(stock=ticker, symbol='资产负债表', indicator='年报')
            if df_balance is not None and not df_balance.empty:
                balance_pivot = df_balance.pivot(index='REPORT_DATE', columns='ITEM_NAME', values='AMOUNT').reset_index()
                balance_pivot['REPORT_DATE'] = pd.to_datetime(balance_pivot['REPORT_DATE'])
                
                for _, row in balance_pivot.iterrows():
                    year = row['REPORT_DATE'].year
                    total_assets = row.get('Total assets') or row.get('资产总计') or 0
                    total_equity = row.get('Stockholders\' equity') or row.get('股东权益合计') or 0
                    total_liab = row.get('Total liabilities') or row.get('负债合计') or 0
                    
                    # 资产负债率
                    if total_assets > 0:
                        debt_ratio = total_liab / total_assets * 100
                        if '资产负债率' not in all_data:
                            all_data['资产负债率'] = {}
                        all_data['资产负债率'][year] = round(debt_ratio, 2)
                    
                    # ROE
                    net_income = all_data.get('净利润', {}).get(year, 0)
                    if total_equity > 0 and net_income > 0:
                        roe = net_income / total_equity * 100
                        if 'ROE' not in all_data:
                            all_data['ROE'] = {}
                        all_data['ROE'][year] = round(roe, 2)
                
                print(f"   ✅ 资产负债表: {len(balance_pivot)} 年数据")
        except Exception as e:
            print(f"   ⚠️ 资产负债表获取失败: {e}")
        
        # 4. 现金流量表数据
        print("\n4. 现金流量表数据:")
        try:
            df_cashflow = ak.stock_financial_us_report_em(stock=ticker, symbol='现金流量表', indicator='年报')
            if df_cashflow is not None and not df_cashflow.empty:
                cf_pivot = df_cashflow.pivot(index='REPORT_DATE', columns='ITEM_NAME', values='AMOUNT').reset_index()
                cf_pivot['REPORT_DATE'] = pd.to_datetime(cf_pivot['REPORT_DATE'])
                
                for _, row in cf_pivot.iterrows():
                    year = row['REPORT_DATE'].year
                    ocf = row.get('Net cash provided by operating activities') or row.get('经营活动产生的现金流量净额') or 0
                    
                    if '经营现金流' not in all_data:
                        all_data['经营现金流'] = {}
                    all_data['经营现金流'][year] = round(ocf / 100000000, 2)  # 亿元
                
                print(f"   ✅ 现金流量表: {len(cf_pivot)} 年数据")
        except Exception as e:
            print(f"   ⚠️ 现金流量表获取失败: {e}")
        
        return all_data
    
    def _collect_cn_financial_data(self, ticker: str) -> Dict[str, Any]:
        """收集 A股财务数据"""
        # TODO: 实现A股数据收集
        return {}
    
    def _collect_from_search(self, company: str, ticker: str) -> Dict[str, Any]:
        """从搜索获取补充数据"""
        # 使用之前的搜索逻辑作为补充
        return {}
    
    def _collect_metric_with_retry(
        self, 
        company: str, 
        ticker: str, 
        metric: str, 
        years: int = 5
    ) -> Optional[Dict]:
        """
        持续尝试收集单个指标数据
        
        策略：
        1. 多种关键词组合
        2. 多个数据源
        3. 多次尝试
        """
        
        # 构建搜索关键词列表
        search_queries = self._build_search_queries(company, ticker, metric, years)
        
        for i, query in enumerate(search_queries):
            print(f"    [{i+1}/{len(search_queries)}] 搜索: {query[:50]}...")
            
            # Tavily 搜索
            if self.tavily_key:
                result = self._search_tavily(query)
                if result:
                    # 尝试从结果中提取数据
                    extracted = self._extract_metric_from_text(result, metric)
                    if extracted:
                        self.search_history.append({
                            "metric": metric,
                            "query": query,
                            "source": "Tavily",
                            "success": True
                        })
                        return extracted
            
            # Exa 搜索
            if self.exa_key:
                result = self._search_exa(query)
                if result:
                    extracted = self._extract_metric_from_text(result, metric)
                    if extracted:
                        self.search_history.append({
                            "metric": metric,
                            "query": query,
                            "source": "Exa",
                            "success": True
                        })
                        return extracted
            
            # 短暂延迟
            time.sleep(0.5)
        
        self.search_history.append({
            "metric": metric,
            "queries": search_queries,
            "success": False
        })
        
        return None
    
    def _build_search_queries(
        self, 
        company: str, 
        ticker: str, 
        metric: str, 
        years: int
    ) -> List[str]:
        """构建多种搜索关键词"""
        
        queries = []
        
        # 中文名
        metric_cn_map = {
            "ROIC": ["ROIC", "投资资本回报率", "投入资本回报率"],
            "ROE": ["ROE", "净资产收益率"],
            "毛利率": ["毛利率", "gross margin", "gross profit margin"],
            "净利率": ["净利率", "net margin", "net profit margin"],
            "营收增速": ["营收增速", "revenue growth", "收入增长率"],
            "净利润增速": ["净利润增速", "net income growth", "利润增长率"],
            "现金周转周期": ["现金周转周期", "cash conversion cycle", "CCC"],
            "销售费用率": ["销售费用率", "sales and marketing expense ratio", "S&M ratio"],
            "经营现金流": ["经营现金流", "operating cash flow", "OCF"],
        }
        
        metric_names = metric_cn_map.get(metric, [metric])
        
        # 英文查询
        for mn in metric_names:
            queries.extend([
                f"{company} {mn} {years} year trend history",
                f"{ticker} {mn} {years} year data",
                f"{company} {mn} 2020 2021 2022 2023 2024",
                f"{ticker} stock {mn} annual data",
                f"{company} {mn} GuruFocus",
                f"{company} {mn} Yahoo Finance",
            ])
        
        # 中文查询
        company_cn = "拼多多" if "pdd" in company.lower() else company
        for mn in metric_names:
            queries.extend([
                f"{company_cn} {mn} 5年 趋势",
                f"{company_cn} {mn} 历史数据",
                f"{ticker} {mn} 年度数据",
            ])
        
        return queries[:10]  # 最多尝试 10 种查询
    
    def _search_tavily(self, query: str) -> Optional[str]:
        """Tavily 搜索"""
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_key,
                    "query": query,
                    "max_results": 8
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    # 合并所有结果
                    combined = "\n".join([
                        f"[{r.get('title', '')}] {r.get('content', '')}"
                        for r in results
                    ])
                    return combined
        except Exception as e:
            pass
        
        return None
    
    def _search_exa(self, query: str) -> Optional[str]:
        """Exa 搜索"""
        try:
            response = requests.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": self.exa_key},
                json={
                    "query": query,
                    "numResults": 8
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results:
                    combined = "\n".join([
                        f"[{r.get('title', '')}] {r.get('text', '')}"
                        for r in results
                    ])
                    return combined
        except Exception as e:
            pass
        
        return None
    
    def _extract_metric_from_text(
        self, 
        text: str, 
        metric: str
    ) -> Optional[Dict]:
        """从文本中提取指标数据"""
        
        import re
        
        # 尝试匹配年份和数值
        year_pattern = r"(20[0-9]{2})"
        
        # 尝试匹配百分比数值
        percent_pattern = r"(\d+\.?\d*)\s*%"
        
        years = re.findall(year_pattern, text)
        values = re.findall(percent_pattern, text)
        
        if years and values:
            # 尝试配对
            result = {}
            for i, year in enumerate(sorted(set(years), reverse=True)[:5]):
                if i < len(values):
                    try:
                        result[year] = float(values[i])
                    except:
                        pass
            
            if result:
                return result
        
        return None
    
    def _collect_xueqiu_data(self, company: str, ticker: str) -> Dict[str, Any]:
        """
        从雪球收集数据
        
        实现需求文档 §2.2 的雪球数据源要求
        严格按 §2.2 质量评估规则过滤 P3/P4 数据
        """
        
        result = {}
        
        # 导入验证器
        from core.financial_data_validator import NegationValidator
        validator = NegationValidator()
        
        # 检查本地雪球数据目录
        xueqiu_dir = Path("/root/.openclaw/workspace/ir-crawler/downloads")
        
        if not xueqiu_dir.exists():
            print("    雪球数据目录不存在")
            return result
        
        # 搜索公司相关的目录
        company_lower = company.lower()
        ticker_lower = ticker.lower() if ticker else ""
        
        for company_dir in xueqiu_dir.iterdir():
            dir_name = company_dir.name.lower()
            
            # 匹配公司名或股票代码
            if company_lower in dir_name or ticker_lower in dir_name:
                print(f"    找到雪球数据: {company_dir.name}")
                
                # 读取财务数据文件
                for file_type in ["annual", "quarterly"]:
                    type_dir = company_dir / file_type
                    if type_dir.exists():
                        for pdf_file in type_dir.glob("*.pdf"):
                            # 提取文件中的数据
                            try:
                                import subprocess
                                content_result = subprocess.run(
                                    ["pdftotext", str(pdf_file), "-"],
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                
                                if content_result.returncode == 0:
                                    content = content_result.stdout
                                    title = pdf_file.stem
                                    
                                    # ★★★ 关键：评估数据质量 ★★★
                                    # 年报/季报按"公告"类型评估
                                    quality, discard = validator.evaluate_xueqiu_data_quality(
                                        "公告",  # 年报/季报固定P1
                                        content,
                                        title
                                    )
                                    
                                    # ★★★ 关键：丢弃 P3/P4 数据 ★★★
                                    if discard:
                                        print(f"      [丢弃] {pdf_file.name}: 质量等级 {quality}")
                                        continue
                                    
                                    print(f"      [保留] {pdf_file.name}: 质量等级 {quality}")
                                    
                                    # 尝试提取财务数据
                                    extracted = self._extract_financial_from_text(content, company)
                                    for key, value in extracted.items():
                                        if key not in result:
                                            value["quality"] = quality
                                            result[key] = value
                                            
                            except Exception as e:
                                print(f"      读取失败: {pdf_file.name}")
        
        # 如果没有本地数据，尝试搜索雪球网页
        if not result:
            print("    本地无雪球数据，尝试搜索...")
            if self.tavily_key:
                search_result = self._search_tavily(f"雪球 {company} {ticker} 财务数据 ROIC ROE 毛利率")
                
                for item in search_result[:5]:
                    content = item.get("content", "")
                    title = item.get("title", "")
                    
                    # ★★★ 关键：评估搜索结果质量 ★★★
                    # 搜索结果按"专栏"类型评估（≥300字符=P0，<300=P2）
                    quality, discard = validator.evaluate_xueqiu_data_quality(
                        "专栏",
                                        content,
                                        title
                                    )
                    
                    # ★★★ 关键：丢弃 P3/P4 数据 ★★★
                    if discard:
                        print(f"      [丢弃] 搜索结果: 质量等级 {quality}")
                        continue
                    
                    print(f"      [保留] 搜索结果: 质量等级 {quality}")
                    
                    extracted = self._extract_financial_from_text(content, company)
                    for key, value in extracted.items():
                        value["quality"] = quality
                        result[key] = value
        
        print(f"    雪球数据收集完成: {len(result)} 条有效数据")
        return result
    
    def _extract_financial_from_text(self, text: str, company: str) -> Dict[str, Dict]:
        """从文本中提取财务数据"""
        
        import re
        
        result = {}
        
        # ROIC 提取
        roic_match = re.search(r'ROIC[^0-9]*(\d+\.?\d*)\s*%', text, re.IGNORECASE)
        if roic_match:
            result['ROIC_搜索'] = {
                "value": float(roic_match.group(1)),
                "source": "雪球搜索",
                "timestamp": datetime.now().isoformat()
            }
        
        # ROE 提取
        roe_match = re.search(r'ROE[^0-9]*(\d+\.?\d*)\s*%', text, re.IGNORECASE)
        if roe_match:
            result['ROE_搜索'] = {
                "value": float(roe_match.group(1)),
                "source": "雪球搜索",
                "timestamp": datetime.now().isoformat()
            }
        
        # 毛利率提取
        gross_match = re.search(r'毛利率[^0-9]*(\d+\.?\d*)\s*%', text)
        if gross_match:
            result['毛利率_搜索'] = {
                "value": float(gross_match.group(1)),
                "source": "雪球搜索",
                "timestamp": datetime.now().isoformat()
            }
        
        return result
    
    def _collect_peer_comparison(
        self, 
        company: str, 
        ticker: str
    ) -> Optional[Dict]:
        """收集同行对比数据"""
        
        # PDD 的同行
        peers = ["Alibaba", "JD.com", "Meituan"] if "pdd" in company.lower() else []
        
        peer_data = {}
        
        for peer in peers:
            query = f"{company} vs {peer} ROIC ROE gross margin comparison"
            result = self._search_tavily(query)
            if result:
                peer_data[peer] = result[:500]
        
        return peer_data if peer_data else None
    
    def get_collection_report(self) -> str:
        """获取数据收集报告"""
        
        report = "# 数据收集报告\n\n"
        
        success = [h for h in self.search_history if h.get("success")]
        failed = [h for h in self.search_history if not h.get("success")]
        
        report += f"## 统计\n\n"
        report += f"- 成功收集: {len(success)} 个指标\n"
        report += f"- 未能收集: {len(failed)} 个指标\n\n"
        
        if failed:
            report += f"## 未收集到的指标\n\n"
            for f in failed:
                report += f"- {f.get('metric', '未知')}\n"
        
        return report


# 测试
if __name__ == "__main__":
    collector = EnhancedDataCollector()
    data = collector.collect_all_financial_data("PDD Holdings", "PDD", "us")
    
    print("\n收集到的数据:")
    for metric, values in data.items():
        print(f"  {metric}: {values}")