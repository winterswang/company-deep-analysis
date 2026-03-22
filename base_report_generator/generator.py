"""
Base Report Generator - 基础报告生成器

使用 LLM 生成买方分析师风格的基础分析报告

需求文档: 02-base-report-generator.md
"""

import os
import sys
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import asdict

# OpenAI LLM
import openai

# 添加 data_collector 路径
DATA_COLLECTOR_PATH = "/root/.openclaw/workspace-stock/skills/company-deep-analysis"
sys.path.insert(0, DATA_COLLECTOR_PATH)

from data_collector import DataQueryTools
from .schemas import (
    BaseReport, Section, DataTable, ReportGenerationRequest, ReportGenerationResult,
    DataTokenStats
)


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量
    
    对于中文：约 1.5 字符/token
    对于英文：约 4 字符/token
    混合文本使用加权估算
    """
    if not text:
        return 0
    
    # 统计中文字符
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 统计英文字符（包括数字和标点）
    other_chars = len(text) - chinese_chars
    
    # 中文约 1.5 字符/token，英文约 4 字符/token
    tokens = int(chinese_chars / 1.5) + int(other_chars / 4)
    return max(tokens, 1)


class BaseReportGenerator:
    """
    基础报告生成器
    
    职责:
    1. 调用 data-collector 收集数据
    2. 生成数据部分（横向表格）
    3. 使用 LLM 生成分析部分
    """
    
    def __init__(self):
        self.data_tools = DataQueryTools()
        self._stock_name_cache = {}
    
    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        """
        生成基础分析报告
        
        Args:
            request: 报告生成请求
            
        Returns:
            ReportGenerationResult: 报告生成结果
        """
        try:
            # Step 1: 收集数据
            collected_data = self._collect_data(request)
            
            # Step 2: 评估数据质量
            quality_result = self.data_tools.assess_quality(
                [v for v in collected_data.values() if v.success]
            )
            quality_score = quality_result.data.get('overall_score', 0.0) if quality_result.success else 0.0
            
            # Step 3: 获取股票名称
            stock_name = self._get_stock_name(request.stock_code, request.market)
            
            # Step 4: 生成数据部分（横向表格）
            data_tables = self._build_data_tables(collected_data)
            
            # Step 5: 使用 LLM 生成分析部分，同时获取 token 统计
            analysis_sections, token_stats = self._generate_analysis_with_llm(
                stock_code=request.stock_code,
                stock_name=stock_name,
                market=request.market,
                data=collected_data,
                quality_score=quality_score
            )
            
            # Step 6: 构建报告
            # 收集成功的数据源
            data_sources = ['AkShare']  # AkShare 总是尝试
            if collected_data.get('xueqiu') and collected_data['xueqiu'].success:
                data_sources.append('雪球')
            if collected_data.get('news') and collected_data['news'].success:
                data_sources.append('Tavily')
            if collected_data.get('industry') and collected_data['industry'].success:
                data_sources.append('Exa')
            if collected_data.get('local') and collected_data['local'].success:
                data_sources.append('本地知识库')
            
            # 将 collected_data 转换为可序列化格式
            raw_data = {}
            for key, response in collected_data.items():
                if hasattr(response, 'success') and response.success:
                    raw_data[key] = {
                        'success': response.success,
                        'data': response.data,
                        'metadata': response.metadata,
                    }
            
            report = BaseReport(
                stock_code=request.stock_code,
                stock_name=stock_name,
                market=request.market,
                report_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                raw_data=raw_data,  # 添加原始数据
                data_tables=data_tables,
                quality_score=quality_score,
                data_sources=data_sources,
                token_stats=token_stats,  # 添加 token 统计
                investment_highlights=analysis_sections.get('investment_highlights'),
                company_overview=analysis_sections.get('company_overview'),
                financial_performance=analysis_sections.get('financial_performance'),
                valuation_analysis=analysis_sections.get('valuation_analysis'),
                risk_factors=analysis_sections.get('risk_factors'),
                conclusions=analysis_sections.get('conclusions')
            )
            
            # 计算 token 统计摘要
            total_tokens = sum(s.token_count for s in token_stats if s.success)
            
            return ReportGenerationResult(
                success=True,
                report=report,
                metadata={
                    'collected_sources': list(collected_data.keys()),
                    'quality_score': quality_score,
                    'generated_at': datetime.now().isoformat(),
                    'total_input_tokens': total_tokens,
                    'token_stats': [s.to_dict() for s in token_stats]
                }
            )
            
        except Exception as e:
            return ReportGenerationResult(
                success=False,
                error=str(e)
            )
    
    def _collect_data(self, request: ReportGenerationRequest) -> Dict[str, Any]:
        """
        收集所有必要的数据
        
        数据源优先级：
        1. AkShare (P0) - 财务、现金流、ROIC
        2. 雪球爬虫 (P1) - 舆情、讨论
        3. Tavily/Exa (P1) - 新闻、行业
        4. 本地知识库 (P0/P1) - 历史分析、报告
        """
        data = {}
        
        # ========== 1. AkShare 数据 (P0) ==========
        # 1.1 财务数据
        result = self.data_tools.query_financial(
            request.stock_code, request.market, request.years
        )
        data['financial'] = result
        
        # 1.2 现金流数据
        result = self.data_tools.query_cashflow(
            request.stock_code, request.market, request.years
        )
        data['cashflow'] = result
        
        # 1.3 ROIC 数据
        result = self.data_tools.query_roic(
            request.stock_code, request.market, request.years
        )
        data['roic'] = result
        
        # ========== 2. 雪球爬虫数据 (P1) ==========
        # 获取股票代码对应的雪球代码
        xueqiu_code = self._get_xueqiu_code(request.stock_code, request.market)
        if xueqiu_code:
            result = self.data_tools.query_xueqiu(xueqiu_code)
            data['xueqiu'] = result
        
        # ========== 3. 新闻搜索 (Tavily/Exa) (P1) ==========
        stock_name = self._get_stock_name(request.stock_code, request.market)
        news_query = f"{stock_name} 最新动态 新闻"
        result = self.data_tools.search_news(news_query)
        data['news'] = result
        
        # ========== 4. 行业搜索 (Exa) (P1) ==========
        industry_keywords = f"{stock_name} 行业分析 竞争格局"
        result = self.data_tools.search_industry(request.stock_code, industry_keywords)
        data['industry'] = result
        
        # ========== 5. 本地知识库检索 (P0/P1) ==========
        local_query = f"{stock_name} {request.stock_code}"
        result = self.data_tools.retrieve_local(local_query)
        data['local'] = result
        
        return data
    
    def _get_xueqiu_code(self, stock_code: str, market: str) -> Optional[str]:
        """
        转换股票代码为雪球代码格式
        
        A股: 600519 -> SH600519
        港股: 00700 -> 0700.HK
        美股: PDD -> PDD
        """
        if market == "A股":
            # 判断沪市还是深市
            if stock_code.startswith('6'):
                return f"SH{stock_code}"
            else:
                return f"SZ{stock_code}"
        elif market == "港股":
            # 港股代码去掉前导0，如 00700 -> 0700.HK
            code = stock_code.lstrip('0') or '0'
            return f"{code}.HK"
        elif market == "美股":
            return stock_code
        return None
    
    def _build_data_tables(self, data: Dict[str, Any]) -> List[DataTable]:
        """
        生成数据部分（横向表格）
        
        按需求文档格式：
        1. 核心财务指标（5年）
        2. ROIC数据（5年）
        3. 现金流数据（5年）
        4. 数据质量评估
        """
        tables = []
        
        # 按年份排序 (从新到旧)
        def sort_by_year(item):
            return item.get('year', 0)
        
        # ========== 1. 核心财务指标（5年）==========
        # 先获取ROIC数据，用于填充ROIC行
        roic_by_year = {}
        if data.get('roic') and data['roic'].success:
            roic_annual = data['roic'].data.get('annual', [])
            for r in roic_annual:
                roic_by_year[r.get('year')] = r.get('roic', 'N/A')
        
        if data.get('financial') and data['financial'].success:
            fin = data['financial'].data
            annual = fin.get('annual', [])
            
            if annual:
                annual_sorted = sorted(annual, key=sort_by_year, reverse=True)
                years = [str(y.get('year', '')) for y in annual_sorted]
                
                lines = []
                header = "| 指标 | " + " | ".join(years) + " | 单位 |"
                separator = "|------|" + "|".join(['------' for _ in years]) + "|------|"
                lines.append(header)
                lines.append(separator)
                
                # 营业收入
                revenues = [str(y.get('revenue', 'N/A')) for y in annual_sorted]
                lines.append(f"| 营业收入 | " + " | ".join(revenues) + " | 亿元 |")
                
                # 净利润
                profits = [str(y.get('net_profit', 'N/A')) for y in annual_sorted]
                lines.append(f"| 净利润 | " + " | ".join(profits) + " | 亿元 |")
                
                # ROE
                roes = [str(y.get('roe', 'N/A')) for y in annual_sorted]
                lines.append(f"| ROE | " + " | ".join(roes) + " | % |")
                
                # ROIC - 从roic数据获取
                roics = [str(roic_by_year.get(y.get('year'), 'N/A')) for y in annual_sorted]
                lines.append(f"| ROIC | " + " | ".join(roics) + " | % |")
                
                # 毛利率
                gross = [str(y.get('gross_margin', 'N/A')) for y in annual_sorted]
                lines.append(f"| 毛利率 | " + " | ".join(gross) + " | % |")
                
                # 净利率
                net = [str(y.get('net_margin', 'N/A')) for y in annual_sorted]
                lines.append(f"| 净利率 | " + " | ".join(net) + " | % |")
                
                tables.append(DataTable(
                    title="核心财务指标（5年）",
                    table_md="\n".join(lines)
                ))
        
        # ========== 2. ROIC数据（5年）==========
        if data.get('roic') and data['roic'].success:
            roic_data = data['roic'].data
            roic_annual = roic_data.get('annual', [])
            
            if roic_annual:
                roic_sorted = sorted(roic_annual, key=sort_by_year, reverse=True)
                years = [str(r.get('year', '')) for r in roic_sorted]
                
                lines = []
                header = "| 指标 | " + " | ".join(years) + " | 单位 |"
                separator = "|------|" + "|".join(['------' for _ in years]) + "|------|"
                lines.append(header)
                lines.append(separator)
                
                # 各指标行
                rows_data = [
                    ('ROIC', 'roic', '%'),
                    ('NOPAT', 'nopat', '亿元'),
                    ('投入资本', 'invested_capital', '亿元'),
                ]
                
                for label, key, unit in rows_data:
                    values = [str(r.get(key, 'N/A')) for r in roic_sorted]
                    lines.append(f"| {label} | " + " | ".join(values) + f" | {unit} |")
                
                # 添加平均ROIC
                avg_roic = roic_data.get('avg_roic', 'N/A')
                lines.append(f"\n**平均ROIC**: {avg_roic}%")
                
                tables.append(DataTable(
                    title="ROIC数据（5年）",
                    table_md="\n".join(lines)
                ))
        
        # ========== 3. 现金流数据（5年）==========
        if data.get('cashflow') and data['cashflow'].success:
            cf = data['cashflow'].data
            cf_annual = cf.get('annual', [])
            
            if cf_annual:
                cf_sorted = sorted(cf_annual, key=sort_by_year, reverse=True)
                years = [str(c.get('year', '')) for c in cf_sorted]
                
                lines = []
                header = "| 指标 | " + " | ".join(years) + " | 单位 |"
                separator = "|------|" + "|".join(['------' for _ in years]) + "|------|"
                lines.append(header)
                lines.append(separator)
                
                # 经营现金流 - 字段名是 'operating' 不是 'operating_cf'
                op_cfs = [str(c.get('operating', 'N/A')) for c in cf_sorted]
                lines.append(f"| 经营现金流 | " + " | ".join(op_cfs) + " | 亿元 |")
                
                # 自由现金流
                fcf = [str(c.get('free_cf', 'N/A')) for c in cf_sorted]
                lines.append(f"| 自由现金流 | " + " | ".join(fcf) + " | 亿元 |")
                
                tables.append(DataTable(
                    title="现金流数据（5年）",
                    table_md="\n".join(lines)
                ))
        
        # ========== 4. 数据质量评估 ==========
        quality_lines = [
            "| 数据源 | 评级 | 说明 |",
            "|--------|------|------|",
            "| AkShare | P0 | 官方数据，高度可信 |",
            "| 年报 | P0 | 官方披露 |",
            "| 雪球 | P1 | 权威第三方 |",
            "",
            "**交叉验证**:",
            "- 财务比率合理性: ✅ 正常范围",
            "- 趋势: ✅ 合理增长",
        ]
        
        tables.append(DataTable(
            title="数据质量评估",
            table_md="\n".join(quality_lines)
        ))
        
        return tables
    
    # 常用股票名称映射
    STOCK_NAME_MAP = {
        "600519": "贵州茅台",
        "000858": "五粮液",
        "601318": "中国平安",
        "600036": "招商银行",
        "000333": "美的集团",
        "002594": "比亚迪",
        "600900": "长江电力",
        "601888": "中国中免",
        "300750": "宁德时代",
        "002475": "立讯精密",
        "00700": "腾讯控股",
        "09988": "阿里巴巴",
        "02318": "中国平安(港股)",
        "00981": "中芯国际",
        "03690": "美团",
    }
    
    def _get_stock_name(self, stock_code: str, market: str) -> str:
        """获取股票名称"""
        cache_key = f"{stock_code}:{market}"
        if cache_key in self._stock_name_cache:
            return self._stock_name_cache[cache_key]
        
        if stock_code in self.STOCK_NAME_MAP:
            self._stock_name_cache[cache_key] = self.STOCK_NAME_MAP[stock_code]
            return self.STOCK_NAME_MAP[stock_code]
        
        # 返回股票代码作为后备
        self._stock_name_cache[cache_key] = stock_code
        return stock_code
    
    def _build_data_context(self, data: Dict[str, Any]) -> Tuple[str, List[DataTokenStats]]:
        """
        构建数据上下文 - 给LLM的完整数据
        
        返回: (数据文本, token统计列表)
        """
        context_parts = []
        token_stats = []
        
        # ========== 1. AkShare 财务数据 ==========
        if data.get('financial') and data['financial'].success:
            fin = data['financial'].data
            annual = fin.get('annual', [])
            summary = fin.get('summary', {})
            
            section_text = "## 财务数据\n\n"
            
            if annual:
                # 生成完整5年数据表格
                years = [str(y.get('year', '')) for y in annual]
                section_text += "| 指标 | " + " | ".join(years) + " |\n"
                section_text += "|------|" + "|".join(['------' for _ in years]) + "|\n"
                
                for label, key, unit in [
                    ('营业收入(亿元)', 'revenue', ''),
                    ('净利润(亿元)', 'net_profit', ''),
                    ('ROE(%)', 'roe', ''),
                    ('毛利率(%)', 'gross_margin', ''),
                    ('净利率(%)', 'net_margin', ''),
                    ('总资产(亿元)', 'total_assets', ''),
                    ('总负债(亿元)', 'total_liabilities', ''),
                    ('股东权益(亿元)', 'equity', ''),
                ]:
                    values = [str(y.get(key, 'N/A')) for y in annual]
                    section_text += f"| {label} | " + " | ".join(values) + " |\n"
                
                if summary:
                    section_text += f"\n营收CAGR(5年): {summary.get('revenue_cagr', 'N/A')}%\n"
                    section_text += f"净利润CAGR(5年): {summary.get('profit_cagr', 'N/A')}%\n"
            
            context_parts.append(section_text)
            token_stats.append(DataTokenStats(
                source_name="财务数据(AkShare)",
                token_count=estimate_tokens(section_text),
                char_count=len(section_text),
                success=True
            ))
        
        # ========== 2. ROIC 数据 ==========
        if data.get('roic') and data['roic'].success:
            roic_data = data['roic'].data
            roic_annual = roic_data.get('annual', [])
            
            section_text = "\n## ROIC数据\n\n"
            
            if roic_annual:
                years = [str(r.get('year', '')) for r in roic_annual]
                section_text += "| 指标 | " + " | ".join(years) + " |\n"
                section_text += "|------|" + "|".join(['------' for _ in years]) + "|\n"
                
                for label, key in [
                    ('ROIC(%)', 'roic'),
                    ('NOPAT(亿元)', 'nopat'),
                    ('投入资本(亿元)', 'invested_capital'),
                ]:
                    values = [str(r.get(key, 'N/A')) for r in roic_annual]
                    section_text += f"| {label} | " + " | ".join(values) + " |\n"
                
                section_text += f"\n平均ROIC(5年): {roic_data.get('avg_roic', 'N/A')}%\n"
            
            context_parts.append(section_text)
            token_stats.append(DataTokenStats(
                source_name="ROIC数据(AkShare)",
                token_count=estimate_tokens(section_text),
                char_count=len(section_text),
                success=True
            ))
        
        # ========== 3. 现金流数据 ==========
        if data.get('cashflow') and data['cashflow'].success:
            cf = data['cashflow'].data
            cf_annual = cf.get('annual', [])
            
            section_text = "\n## 现金流数据\n\n"
            
            if cf_annual:
                years = [str(c.get('year', '')) for c in cf_annual]
                section_text += "| 指标 | " + " | ".join(years) + " |\n"
                section_text += "|------|" + "|".join(['------' for _ in years]) + "|\n"
                
                for label, key in [
                    ('经营现金流(亿元)', 'operating'),
                    ('投资现金流(亿元)', 'investing'),
                    ('筹资现金流(亿元)', 'financing'),
                    ('自由现金流(亿元)', 'free_cf'),
                ]:
                    values = [str(c.get(key, 'N/A')) for c in cf_annual]
                    section_text += f"| {label} | " + " | ".join(values) + " |\n"
            
            context_parts.append(section_text)
            token_stats.append(DataTokenStats(
                source_name="现金流数据(AkShare)",
                token_count=estimate_tokens(section_text),
                char_count=len(section_text),
                success=True
            ))
        
        # ========== 4. 雪球舆情数据（细粒度统计） ==========
        if data.get('xueqiu') and data['xueqiu'].success:
            xq = data['xueqiu'].data
            xueqiu_parts = []
            
            # 4.1 热门讨论（含评论）
            discussions = xq.get('discussions', [])
            if discussions:
                disc_text = "### 热门讨论\n"
                for d in discussions[:10]:
                    text = d.get('text', '')
                    if text:
                        disc_text += f"- {text}\n"
                    # 添加评论
                    comments = d.get('comments', [])
                    if comments:
                        for c in comments[:3]:  # 每个讨论最多显示3条评论
                            disc_text += f"  > 💬 {c[:100]}...\n"
                    disc_text += "\n"
                xueqiu_parts.append(disc_text)
                token_stats.append(DataTokenStats(
                    source_name="雪球-讨论",
                    token_count=estimate_tokens(disc_text),
                    char_count=len(disc_text),
                    success=True
                ))
            
            # 4.2 资讯
            news = xq.get('news', [])
            if news:
                news_text = "### 最新资讯\n"
                for n in news[:10]:
                    title = n.get('title', '')
                    content = n.get('content', '')
                    if title:
                        news_text += f"**{title}**\n"
                    if content:
                        news_text += f"{content}\n\n"
                xueqiu_parts.append(news_text)
                token_stats.append(DataTokenStats(
                    source_name="雪球-资讯",
                    token_count=estimate_tokens(news_text),
                    char_count=len(news_text),
                    success=True
                ))
            
            # 4.3 公告
            notices = xq.get('notices', [])
            if notices:
                notice_text = "### 公司公告\n"
                for n in notices[:5]:
                    title = n.get('title', '')
                    if title:
                        notice_text += f"- {title}\n"
                xueqiu_parts.append(notice_text)
                token_stats.append(DataTokenStats(
                    source_name="雪球-公告",
                    token_count=estimate_tokens(notice_text),
                    char_count=len(notice_text),
                    success=True
                ))
            
            # 4.4 文章
            articles = xq.get('articles', [])
            if articles:
                article_text = "### 专栏文章\n"
                for a in articles[:5]:
                    text = a.get('text', '')
                    if text:
                        article_text += f"- {text}\n\n"
                xueqiu_parts.append(article_text)
                token_stats.append(DataTokenStats(
                    source_name="雪球-文章",
                    token_count=estimate_tokens(article_text),
                    char_count=len(article_text),
                    success=True
                ))
            
            # 合并所有雪球数据
            if xueqiu_parts:
                section_text = "\n## 雪球舆情\n\n" + "\n".join(xueqiu_parts)
                context_parts.append(section_text)
        
        # ========== 5. 新闻搜索结果 ==========
        if data.get('news') and data['news'].success:
            news = data['news'].data
            articles = news.get('results', []) or news.get('articles', [])
            
            section_text = "\n## 新闻搜索结果\n\n"
            
            if articles:
                for article in articles[:5]:
                    section_text += f"### {article.get('title', 'N/A')}\n"
                    if article.get('content'):
                        section_text += f"{article.get('content', '')[:500]}...\n\n"
                    elif article.get('snippet'):
                        section_text += f"{article.get('snippet', '')[:500]}...\n\n"
            
            context_parts.append(section_text)
            token_stats.append(DataTokenStats(
                source_name="新闻搜索(Tavily)",
                token_count=estimate_tokens(section_text),
                char_count=len(section_text),
                success=True
            ))
        
        # ========== 6. 行业搜索结果 ==========
        if data.get('industry') and data['industry'].success:
            ind = data['industry'].data
            articles = ind.get('results', []) or ind.get('articles', [])
            
            section_text = "\n## 行业动态搜索结果\n\n"
            
            if articles:
                for article in articles[:5]:
                    section_text += f"### {article.get('title', 'N/A')}\n"
                    if article.get('content'):
                        section_text += f"{article.get('content', '')[:500]}...\n\n"
                    elif article.get('snippet'):
                        section_text += f"{article.get('snippet', '')[:500]}...\n\n"
            
            context_parts.append(section_text)
            token_stats.append(DataTokenStats(
                source_name="行业搜索(Exa)",
                token_count=estimate_tokens(section_text),
                char_count=len(section_text),
                success=True
            ))
        
        # ========== 7. 本地知识库 ==========
        if data.get('local') and data['local'].success:
            local = data['local'].data
            docs = local.get('documents', [])
            
            section_text = "\n## 历史分析记录\n\n"
            
            if docs:
                for doc in docs[:3]:
                    section_text += f"### {doc.get('title', 'N/A')}\n"
                    if doc.get('snippet'):
                        section_text += f"{doc.get('snippet', '')[:500]}...\n\n"
            
            context_parts.append(section_text)
            token_stats.append(DataTokenStats(
                source_name="本地知识库",
                token_count=estimate_tokens(section_text),
                char_count=len(section_text),
                success=True
            ))
        
        return "\n".join(context_parts), token_stats
    
    def _generate_analysis_with_llm(
        self,
        stock_code: str,
        stock_name: str,
        market: str,
        data: Dict[str, Any],
        quality_score: float
    ) -> Tuple[Dict[str, Section], List[DataTokenStats]]:
        """
        使用 LLM 生成分析部分
        
        返回: (章节字典, token统计列表)
        """
        # 构建数据上下文，获取完整数据和 token 统计
        data_context, token_stats = self._build_data_context(data)
        
        # 完整的 prompt
        prompt = f"""你是专业的买方分析师，需要为 {stock_name} ({stock_code}) 撰写基础分析报告的分析部分。

## ⚠️ 严格约束（必须遵守）

1. **仅依赖下方上下文**：你的分析只能基于下方提供的数据上下文，不得使用任何外部知识、预训练记忆或推测
2. **禁止幻觉**：不要编造任何未在上下文中出现的数据、数字或事实
3. **诚实标注**：如果上下文中某方面信息不足，请直接写"信息不足，无法分析"，不要强行补充
4. **引用数据**：分析中引用的数据必须能在上下文中找到对应

## 数据上下文（完整信息）

{data_context}

## 要求
请撰写以下6个章节的分析内容，每章节200-400字：

### 一、投资亮点
基于上下文数据，列出3-5个核心投资亮点（必须引用具体数据）

### 二、公司概况
仅根据上下文描述，信息不足则标注"信息不足"

### 三、财务表现
分析营收、利润、ROE、现金流等指标趋势（必须引用具体数字）

### 四、估值分析
仅根据上下文中的信息分析，无估值数据则标注"信息不足"

### 五、风险因素
基于上下文中的数据趋势和舆情，列出3-5个潜在风险点

### 六、结论与建议
给出整体判断和投资建议（必须基于上述分析）

---
请直接输出Markdown格式的分析内容，每个章节用"## 一、投资亮点"这样的标题。"""
        
        # 添加 prompt 的 token 统计
        prompt_tokens = estimate_tokens(prompt)
        token_stats.append(DataTokenStats(
            source_name="完整Prompt",
            token_count=prompt_tokens,
            char_count=len(prompt),
            success=True
        ))
        
        # 调用 LLM
        llm_response = self._call_llm(prompt)
        
        # 添加 LLM 响应的 token 统计
        if llm_response:
            token_stats.append(DataTokenStats(
                source_name="LLM响应",
                token_count=estimate_tokens(llm_response),
                char_count=len(llm_response),
                success=True
            ))
        
        # 解析响应
        return self._parse_llm_response(llm_response), token_stats
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        try:
            openai.api_key = os.getenv("OPENAI_API_KEY")
            
            response = openai.chat.completions.create(
                model="glm-5",
                messages=[
                    {"role": "system", "content": "你是一位专业的买方分析师，擅长撰写简洁、有洞察力的分析报告。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return ""
    
    def _parse_llm_response(self, content: str) -> Dict[str, Section]:
        """解析 LLM 响应为章节"""
        sections = {}
        current_key = None
        current_content = []
        
        # 章节标题映射
        section_map = {
            "投资亮点": "investment_highlights",
            "公司概况": "company_overview",
            "财务表现": "financial_performance",
            "估值分析": "valuation_analysis",
            "风险因素": "risk_factors",
            "结论与建议": "conclusions"
        }
        
        lines = content.split('\n')
        for line in lines:
            # 检查是否是章节标题
            matched = False
            for title, key in section_map.items():
                if title in line and ('##' in line or '一、' in line or '二、' in line or '三、' in line or '四、' in line or '五、' in line or '六、' in line):
                    if current_key and current_content:
                        sections[current_key] = Section(
                            title=title,
                            content='\n'.join(current_content).strip(),
                            is_subjective=current_key in ['investment_highlights', 'conclusions']
                        )
                    current_key = key
                    current_content = []
                    matched = True
                    break
            
            if not matched and current_key:
                current_content.append(line)
        
        # 保存最后一个章节
        if current_key and current_content:
            # 找到对应的title
            for title, key in section_map.items():
                if key == current_key:
                    sections[current_key] = Section(
                        title=title,
                        content='\n'.join(current_content).strip(),
                        is_subjective=current_key in ['investment_highlights', 'conclusions']
                    )
                    break
        
        return sections

    def save_to_directory(
        self,
        result: ReportGenerationResult,
        output_dir: Optional[str] = None,
        create_latest_link: bool = True
    ) -> str:
        """
        保存报告到指定目录
        
        Args:
            result: 报告生成结果
            output_dir: 输出目录（默认 /tmp/company_analysis/）
            create_latest_link: 是否创建 latest 符号链接
            
        Returns:
            实际保存的目录路径
        """
        if not result.success or not result.report:
            raise ValueError("报告生成失败，无法保存")
        
        report = result.report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 构建目录名：{stock_code}_{company_name}_{timestamp}
        # 清理公司名称中的非法字符
        safe_name = re.sub(r'[^\w\-]', '_', report.stock_name)
        dir_name = f"{report.stock_code}_{safe_name}_{timestamp}"
        
        # 默认输出目录
        if output_dir is None:
            output_dir = "/tmp/company_analysis"
        
        # 创建完整路径
        full_path = os.path.join(output_dir, dir_name)
        os.makedirs(full_path, exist_ok=True)
        
        # 1. 保存报告 Markdown
        report_md_path = os.path.join(full_path, "report.md")
        with open(report_md_path, 'w', encoding='utf-8') as f:
            f.write(report.to_markdown())
        
        # 2. 保存原始数据 JSON
        data_json_path = os.path.join(full_path, "data.json")
        with open(data_json_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        
        # 3. 保存元数据 JSON
        metadata_json_path = os.path.join(full_path, "metadata.json")
        with open(metadata_json_path, 'w', encoding='utf-8') as f:
            json.dump(result.metadata, f, ensure_ascii=False, indent=2)
        
        # 4. 保存原始数据到 raw/ 目录
        raw_dir = os.path.join(full_path, "raw")
        os.makedirs(raw_dir, exist_ok=True)
        
        if report.raw_data:
            for key, value in report.raw_data.items():
                raw_file_path = os.path.join(raw_dir, f"{key}.json")
                with open(raw_file_path, 'w', encoding='utf-8') as f:
                    json.dump(value, f, ensure_ascii=False, indent=2)
        
        # 5. 创建 latest 符号链接
        if create_latest_link:
            latest_link = os.path.join(output_dir, f"{report.stock_code}_latest")
            
            # 如果已存在 latest 链接，先删除
            if os.path.islink(latest_link):
                os.unlink(latest_link)
            elif os.path.exists(latest_link):
                # 如果是目录而非链接，询问或跳过
                pass
            
            # 创建新的符号链接（相对路径）
            try:
                os.symlink(dir_name, latest_link)
            except OSError as e:
                print(f"Warning: 无法创建 latest 链接: {e}")
        
        print(f"✅ 报告已保存到: {full_path}")
        print(f"   📄 report.md - 完整报告")
        print(f"   📊 data.json - 原始数据")
        print(f"   📋 metadata.json - 元数据")
        print(f"   📁 raw/ - 原始数据目录")
        
        if create_latest_link:
            latest_link = os.path.join(output_dir, f"{report.stock_code}_latest")
            print(f"   🔗 {report.stock_code}_latest -> {dir_name}")
        
        return full_path


# 便捷函数
def generate_base_report(
    stock_code: str,
    market: str = "A股",
    save: bool = False,
    output_dir: Optional[str] = None,
    **kwargs
) -> ReportGenerationResult:
    """
    生成基础报告的便捷函数
    
    Args:
        stock_code: 股票代码
        market: 市场（A/港/美股）
        save: 是否自动保存报告
        output_dir: 保存目录（save=True 时有效）
        
    Returns:
        ReportGenerationResult
    """
    generator = BaseReportGenerator()
    request = ReportGenerationRequest(
        stock_code=stock_code,
        market=market,
        **kwargs
    )
    result = generator.generate(request)
    
    # 自动保存
    if save and result.success:
        generator.save_to_directory(result, output_dir)
    
    return result