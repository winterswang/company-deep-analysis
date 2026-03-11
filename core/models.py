"""
V5.0 核心数据结构
迭代式辩证分析框架
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class DoubtType(Enum):
    """疑点类型"""
    DATA_CONTRADICTION = "数据矛盾"
    LOGIC_GAP = "逻辑断裂"
    COUNTEREXAMPLE = "反例存在"
    MISSING_INFO = "信息缺失"
    STRONG_ASSUMPTION = "假设过强"


class Priority(Enum):
    """优先级"""
    P0 = "核心结论影响"
    P1 = "次要结论影响"
    P2 = "补充性信息"


class DoubtStatus(Enum):
    """疑点状态"""
    PENDING = "待验证"
    RESOLVED = "已解决"
    PARTIALLY_RESOLVED = "部分解决"
    UNRESOLVABLE = "无法验证"


class CredibilityLevel(Enum):
    """证据可信度"""
    P0_OFFICIAL = "官方文件"
    P1_AUTHORITY = "权威媒体"
    P2_PROFESSIONAL = "专业分析"
    P3_GENERAL = "大众媒体"
    P4_SOCIAL = "社交媒体"


class EvidenceDirection(Enum):
    """证据方向"""
    SUPPORT = "支持"
    REFUTE = "否定"
    NEUTRAL = "中立"
    UNCLEAR = "不明确"


class DataSource(Enum):
    """数据源"""
    AKSHARE = "akshare"
    XUEQIU = "xueqiu"
    TAVILY = "tavily"
    EXA = "exa"
    WEB_FETCH = "web_fetch"


@dataclass
class Doubt:
    """疑点"""
    id: str
    type: DoubtType
    description: str
    priority: Priority
    status: DoubtStatus = DoubtStatus.PENDING
    reason: str = ""  # 为什么这是个问题
    expected_evidence: str = ""  # 期望什么证据
    resolution: Optional[str] = None  # 解决方案/结论
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "reason": self.reason,
            "expected_evidence": self.expected_evidence,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class SearchTarget:
    """检索目标"""
    id: str
    doubt_id: str
    purpose: str  # 检索目的
    query: str  # 搜索查询
    data_source: DataSource  # 数据源
    expected_result: str  # 期望结果
    status: str = "pending"  # pending/completed/failed
    results: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "doubt_id": self.doubt_id,
            "purpose": self.purpose,
            "query": self.query,
            "data_source": self.data_source.value,
            "expected_result": self.expected_result,
            "status": self.status,
            "results": self.results,
        }


@dataclass
class Evidence:
    """证据"""
    id: str
    source: str  # 来源URL/文档
    source_type: str  # 来源类型
    credibility: CredibilityLevel
    content: str  # 内容摘要
    relevance: float  # 相关性 0-1
    direction: EvidenceDirection
    doubt_id: str = ""  # 关联的疑点ID
    extracted_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "source_type": self.source_type,
            "credibility": self.credibility.value,
            "content": self.content,
            "relevance": self.relevance,
            "direction": self.direction.value,
            "doubt_id": self.doubt_id,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None,
        }


@dataclass
class Hypothesis:
    """假设"""
    version: int
    content: str  # 假设内容
    confidence: float  # 置信度 0-1
    supporting_evidences: List[str] = field(default_factory=list)  # 支持证据ID列表
    open_doubts: List[str] = field(default_factory=list)  # 未解决疑点ID列表
    resolved_doubts: List[str] = field(default_factory=list)  # 已解决疑点ID列表
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "content": self.content,
            "confidence": self.confidence,
            "supporting_evidences": self.supporting_evidences,
            "open_doubts": self.open_doubts,
            "resolved_doubts": self.resolved_doubts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class AnalysisScore:
    """分析评分"""
    hypothesis_completeness: int  # 假设完整性 /25
    evidence_sufficiency: int  # 证据充分性 /25
    doubt_resolution_rate: int  # 疑点解决率 /25
    logic_consistency: int  # 逻辑一致性 /15
    depth_analysis: int  # 深度分析 /10
    comments: str = ""  # 评分说明
    
    @property
    def total(self) -> int:
        return (
            self.hypothesis_completeness +
            self.evidence_sufficiency +
            self.doubt_resolution_rate +
            self.logic_consistency +
            self.depth_analysis
        )
    
    def is_sufficient(self, threshold: int = 85) -> bool:
        """判断分析是否充分"""
        return self.total >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_completeness": self.hypothesis_completeness,
            "evidence_sufficiency": self.evidence_sufficiency,
            "doubt_resolution_rate": self.doubt_resolution_rate,
            "logic_consistency": self.logic_consistency,
            "depth_analysis": self.depth_analysis,
            "total": self.total,
            "is_sufficient": self.is_sufficient(),
            "comments": self.comments,
        }


@dataclass
class IterationResult:
    """单轮迭代结果"""
    iteration: int
    hypothesis: Hypothesis
    score: AnalysisScore
    doubts: List[Doubt]
    search_targets: List[SearchTarget]
    evidences: List[Evidence]
    skeptic_output: str = ""  # 质疑者输出
    resolver_output: str = ""  # 解决者输出
    should_continue: bool = True  # 是否继续迭代
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "hypothesis": self.hypothesis.to_dict(),
            "score": self.score.to_dict(),
            "doubts": [d.to_dict() for d in self.doubts],
            "search_targets": [s.to_dict() for s in self.search_targets],
            "evidences": [e.to_dict() for e in self.evidences],
            "skeptic_output": self.skeptic_output,
            "resolver_output": self.resolver_output,
            "should_continue": self.should_continue,
        }


@dataclass
class AnalysisChain:
    """完整分析链路"""
    company: str
    company_name: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    iterations: List[IterationResult] = field(default_factory=list)
    final_hypothesis: Optional[Hypothesis] = None
    final_score: Optional[AnalysisScore] = None
    all_doubts: List[Doubt] = field(default_factory=list)
    all_evidences: List[Evidence] = field(default_factory=list)
    all_searches: List[SearchTarget] = field(default_factory=list)
    
    @property
    def total_iterations(self) -> int:
        return len(self.iterations)
    
    @property
    def resolved_doubts_count(self) -> int:
        return len([d for d in self.all_doubts if d.status == DoubtStatus.RESOLVED])
    
    @property
    def resolution_rate(self) -> float:
        if not self.all_doubts:
            return 0.0
        return self.resolved_doubts_count / len(self.all_doubts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company": self.company,
            "company_name": self.company_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_iterations": self.total_iterations,
            "resolved_doubts_count": self.resolved_doubts_count,
            "resolution_rate": self.resolution_rate,
            "final_score": self.final_score.to_dict() if self.final_score else None,
            "iterations": [i.to_dict() for i in self.iterations],
        }