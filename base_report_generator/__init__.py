"""
Base Report Generator - 基础报告生成器

生成买方分析师风格的基础分析报告
"""

from .generator import BaseReportGenerator, generate_base_report
from .schemas import BaseReport, Section

__all__ = ['BaseReportGenerator', 'generate_base_report', 'BaseReport', 'Section']