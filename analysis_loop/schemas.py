"""
Analysis Engine Schemas - 分析引擎数据模型

定义分析引擎的数据结构和输出格式

需求文档: 03-analysis-engine.md
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QuestionAnswer:
    """问题-答案一轮"""
    round: int
    question: str
    answer: str
    score: int  # 0-100
    feedback: str  # 评分反馈
    data_request: Optional[str] = None  # 需要补充的数据请求


@dataclass
class DimensionAnalysis:
    """单个分析维度"""
    dimension: str  # financial_anomaly, business_insight, moat_identification, sustainability
    status: str  # pending, in_progress, completed
    rounds: int = 0
    final_score: int = 0
    questions: List[QuestionAnswer] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)  # 核心洞察
    conclusion: str = ""  # 最终结论
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "status": self.status,
            "rounds": self.rounds,
            "final_score": self.final_score,
            "questions": [
                {
                    "round": qa.round,
                    "question": qa.question,
                    "answer": qa.answer,
                    "score": qa.score,
                    "feedback": qa.feedback,
                    "data_request": qa.data_request
                }
                for qa in self.questions
            ],
            "insights": self.insights,
            "conclusion": self.conclusion
        }


@dataclass
class AnalysisEngineResult:
    """分析引擎输出结果"""
    skill: str = "analysis-engine"
    version: str = "1.0"
    company: str = ""
    stock_code: str = ""
    analysis_date: str = ""
    
    # 各维度分析结果
    dimensions: List[DimensionAnalysis] = field(default_factory=list)
    
    # 汇总洞察
    summary_insights: List[str] = field(default_factory=list)
    overall_score: int = 0  # 所有维度平均分
    
    # 元数据
    total_rounds: int = 0  # 总循环次数
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill": self.skill,
            "version": self.version,
            "company": self.company,
            "stock_code": self.stock_code,
            "analysis_date": self.analysis_date,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "summary_insights": self.summary_insights,
            "overall_score": self.overall_score,
            "total_rounds": self.total_rounds,
            "total_tokens": self.total_tokens
        }


# 分析维度常量
DIMENSION_FINANCIAL_ANOMALY = "financial_anomaly"
DIMENSION_BUSINESS_INSIGHT = "business_insight"
DIMENSION_MOAT_IDENTIFICATION = "moat_identification"
DIMENSION_SUSTAINABILITY = "sustainability"

ALL_DIMENSIONS = [
    DIMENSION_FINANCIAL_ANOMALY,
    DIMENSION_BUSINESS_INSIGHT,
    DIMENSION_MOAT_IDENTIFICATION,
    DIMENSION_SUSTAINABILITY
]

# 维度中文名称
DIMENSION_NAMES = {
    DIMENSION_FINANCIAL_ANOMALY: "财务异常分析",
    DIMENSION_BUSINESS_INSIGHT: "经营洞察分析",
    DIMENSION_MOAT_IDENTIFICATION: "护城河识别",
    DIMENSION_SUSTAINABILITY: "可持续性评估"
}

# 维度主题问题
DIMENSION_QUESTIONS = {
    DIMENSION_FINANCIAL_ANOMALY: "财务比率为什么这样？异常点在哪里？",
    DIMENSION_BUSINESS_INSIGHT: "经营的核心能力是什么？如何赚钱？",
    DIMENSION_MOAT_IDENTIFICATION: "竞争优势是什么？对手能复制吗？",
    DIMENSION_SUSTAINABILITY: "能持续 5-10 年吗？长坡后雪吗？"
}

# 维度优先数据源
DIMENSION_DATA_SOURCES = {
    DIMENSION_FINANCIAL_ANOMALY: ["report.md", "financial_5y.json"],
    DIMENSION_BUSINESS_INSIGHT: ["annual_*_business.md"],
    DIMENSION_MOAT_IDENTIFICATION: ["xueqiu_articles.json"],
    DIMENSION_SUSTAINABILITY: ["news.json", "announcements.json"]
}