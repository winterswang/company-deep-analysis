"""
Base Report Schemas - 基础报告数据模型

定义报告结构和字段

需求文档: 02-base-report-generator.md
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DataTokenStats:
    """数据源 Token 统计"""
    source_name: str  # 数据源名称
    token_count: int  # token 数量
    char_count: int  # 字符数
    success: bool = True  # 是否成功获取
    error: Optional[str] = None  # 错误信息
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_name": self.source_name,
            "token_count": self.token_count,
            "char_count": self.char_count,
            "success": self.success,
            "error": self.error
        }


@dataclass
class Section:
    """报告章节"""
    title: str
    content: str
    is_subjective: bool = False  # 是否为主观判断
    data_source: Optional[str] = None  # 数据来源
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataTable:
    """数据表格"""
    title: str  # 表格标题
    table_md: str  # Markdown格式的表格内容


@dataclass
class BaseReport:
    """
    基础分析报告
    
    报告结构（按需求文档02-base-report-generator.md）：
    
    1. 数据部分（代码生成，横向表格）：
       - 核心财务指标（5年）
       - ROIC数据（5年）
       - 现金流数据（5年）
       - 数据质量评估
    
    2. 分析部分（LLM生成）：
       - 一、投资亮点（主观）
       - 二、公司概况（客观）
       - 三、财务表现（客观）
       - 四、估值分析（客观）
       - 五、风险因素（客观）
       - 六、结论与建议（主观）
    """
    stock_code: str
    stock_name: str
    market: str
    report_date: str
    
    # 数据部分（横向表格）
    data_tables: List[DataTable] = field(default_factory=list)  # 数据表格列表
    quality_score: float = 0.0  # 数据质量评分
    data_sources: List[str] = field(default_factory=list)  # 数据来源
    token_stats: List[DataTokenStats] = field(default_factory=list)  # Token 统计
    
    # 分析部分（LLM生成）
    investment_highlights: Optional[Section] = None  # 投资亮点 (主观)
    company_overview: Optional[Section] = None  # 公司概况 (客观)
    financial_performance: Optional[Section] = None  # 财务表现 (客观)
    valuation_analysis: Optional[Section] = None  # 估值分析 (客观)
    risk_factors: Optional[Section] = None  # 风险因素 (客观)
    conclusions: Optional[Section] = None  # 结论与建议 (主观)
    
    # 元数据
    analyst_notes: Optional[str] = None
    
    def to_markdown(self) -> str:
        """
        转换为 Markdown 格式
        
        按需求文档格式输出：
        1. 标题 + 元信息
        2. 数据部分（横向表格）
        3. 分析部分（LLM生成）
        """
        lines = [
            f"# {self.stock_name} 基础分析报告",
            "",
            f"**生成时间**: {self.report_date}",
            f"**数据质量评分**: {self.quality_score:.2f}/1.00",
            f"**数据来源**: {', '.join(self.data_sources) if self.data_sources else 'AkShare'}",
            "",
        ]
        
        # === Token 统计表格 ===
        if self.token_stats:
            lines.append("## 数据源 Token 统计")
            lines.append("")
            lines.append("| 数据源 | Tokens | 字符数 | 状态 |")
            lines.append("|--------|--------|--------|------|")
            total_tokens = 0
            total_chars = 0
            for stat in self.token_stats:
                status = "✅" if stat.success else "❌"
                lines.append(f"| {stat.source_name} | {stat.token_count:,} | {stat.char_count:,} | {status} |")
                total_tokens += stat.token_count if stat.success else 0
                total_chars += stat.char_count if stat.success else 0
            lines.append(f"| **合计** | **{total_tokens:,}** | **{total_chars:,}** | - |")
            lines.append("")
        
        lines.extend([
            "---",
            "",
        ])
        
        # === 数据部分（横向表格）===
        lines.append("# 数据部分")
        lines.append("")
        
        for table in self.data_tables:
            lines.append(f"## {table.title}")
            lines.append("")
            lines.append(table.table_md)
            lines.append("")
        
        # === 分析部分（LLM生成）===
        lines.append("---")
        lines.append("")
        lines.append("# 分析部分")
        lines.append("")
        
        # 一、投资亮点
        if self.investment_highlights:
            lines.extend([
                "## 一、投资亮点",
                "",
                self.investment_highlights.content,
                "",
            ])
        
        # 二、公司概况
        if self.company_overview:
            lines.extend([
                "## 二、公司概况",
                "",
                self.company_overview.content,
                "",
            ])
        
        # 三、财务表现
        if self.financial_performance:
            lines.extend([
                "## 三、财务表现",
                "",
                self.financial_performance.content,
                "",
            ])
        
        # 四、估值分析
        if self.valuation_analysis:
            lines.extend([
                "## 四、估值分析",
                "",
                self.valuation_analysis.content,
                "",
            ])
        
        # 五、风险因素
        if self.risk_factors:
            lines.extend([
                "## 五、风险因素",
                "",
                self.risk_factors.content,
                "",
            ])
        
        # 六、结论与建议
        if self.conclusions:
            lines.extend([
                "## 六、结论与建议",
                "",
                self.conclusions.content,
                "",
            ])
        
        # 结尾
        lines.extend([
            "---",
            "",
            "*本报告由 Company Deep Analysis 自动生成*",
            "",
        ])
        
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "market": self.market,
            "report_date": self.report_date,
            "data_tables": [
                {"title": t.title, "table_md": t.table_md}
                for t in self.data_tables
            ],
            "quality_score": self.quality_score,
            "data_sources": self.data_sources,
            "sections": {
                "investment_highlights": self.investment_highlights.content if self.investment_highlights else None,
                "company_overview": self.company_overview.content if self.company_overview else None,
                "financial_performance": self.financial_performance.content if self.financial_performance else None,
                "valuation_analysis": self.valuation_analysis.content if self.valuation_analysis else None,
                "risk_factors": self.risk_factors.content if self.risk_factors else None,
                "conclusions": self.conclusions.content if self.conclusions else None,
            },
        }


@dataclass
class ReportGenerationRequest:
    """报告生成请求"""
    stock_code: str
    market: str = "A股"
    years: int = 5  # 财务数据年份
    include_xueqiu: bool = False  # 是否包含雪球数据
    include_search: bool = False  # 是否包含搜索数据
    include_local: bool = False  # 是否包含本地知识库


@dataclass
class ReportGenerationResult:
    """报告生成结果"""
    success: bool
    report: Optional[BaseReport] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)