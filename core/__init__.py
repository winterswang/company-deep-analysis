"""
V5.0 迭代式辩证分析框架
"""

from .models import (
    Doubt, DoubtType, DoubtStatus, Priority,
    SearchTarget, Evidence, EvidenceDirection, CredibilityLevel, DataSource,
    Hypothesis, AnalysisScore, IterationResult, AnalysisChain
)
from .llm_client import LLMClient, SkepticLLM, ResolverLLM
from .iterative_analyzer import IterativeDialecticalAnalyzer, analyze_company

__all__ = [
    # Models
    "Doubt", "DoubtType", "DoubtStatus", "Priority",
    "SearchTarget", "Evidence", "EvidenceDirection", "CredibilityLevel", "DataSource",
    "Hypothesis", "AnalysisScore", "IterationResult", "AnalysisChain",
    # LLM
    "LLMClient", "SkepticLLM", "ResolverLLM",
    # Analyzer
    "IterativeDialecticalAnalyzer", "analyze_company",
]